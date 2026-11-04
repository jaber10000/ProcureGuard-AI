"""Processing service: one PDF in, one independent record out."""
from __future__ import annotations
from pathlib import Path
from .pipeline import run_pipeline, Finding
from .store import Store, sha256

MAX_BULK = 10
MAX_PDF_BYTES = 15 * 1024 * 1024

# Rule groups shown on the "all rules" panel. A group passes when no finding uses its prefix.
RULE_GROUPS = [
    ('PRICE', 'Unit price within PR maximum (3% tolerance)'),
    ('QTY', 'Quantity within 5% of requested quantity'),
    ('PAY', 'Advance ≤ 20% and payment 30–60 days after delivery'),
    ('DEL', 'Delivery ≤ 30 days and late-delivery penalty ≥ 0.5% per week'),
    ('TAX', 'Supplier TIN and BIN present'),
    ('VAT', 'VAT shown separately at 15%'),
    ('MATH', 'Line total, subtotal and total add up'),
    ('QUO', 'Quotation valid for at least 30 days'),
]


def process_upload(store: Store, request: dict, file_name: str, data: bytes, source: str = 'upload', actor: str = 'uploader') -> dict:
    """Process a single PDF. Never raises: a failure only affects this file."""
    out = {'file_name': file_name, 'outcome': 'failed', 'doc_id': None, 'decision': '', 'message': ''}
    try:
        if not data[:5] == b'%PDF-':
            out['message'] = 'Not a valid PDF file.'
            store.log(actor, 'UPLOAD_FAILED', None, f'{file_name}: not a PDF')
            return out
        if len(data) > MAX_PDF_BYTES:
            out['message'] = f'File is larger than {MAX_PDF_BYTES // (1024 * 1024)} MB.'
            store.log(actor, 'UPLOAD_FAILED', None, f'{file_name}: too large')
            return out
        digest = sha256(data)
        existing = store.find_by_hash(digest)
        if existing:
            out.update(outcome='duplicate', doc_id=existing['id'],
                       message=f"Duplicate: identical to already uploaded file “{existing['file_name']}”. No new record was created.")
            store.log(actor, 'DUPLICATE_BLOCKED', existing['id'], f'{file_name} matches document #{existing["id"]}')
            return out
        path = store.pdf_path(digest)
        path.write_bytes(data)
        try:
            result = run_pipeline(path, request)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        result.file_name = file_name
        _apply_no_guessing(result)
        doc_id = store.add_document(file_name, digest, result.to_dict(), source, actor)
        out.update(outcome='processed', doc_id=doc_id, decision=result.decision, message='Processed.')
    except Exception as exc:  # isolate failures per file
        out['message'] = f'Processing failed: {type(exc).__name__}: {exc}'
        try:
            store.log(actor, 'UPLOAD_FAILED', None, f'{file_name}: {type(exc).__name__}: {exc}')
        except Exception:
            pass
    return out


def _apply_no_guessing(result) -> None:
    """If the PDF has no recognisable quotation content, never guess: route to Human Review."""
    if result.item_code or result.quotation_no:
        return
    snippet = ' '.join(result.extracted_text.split())[:160] or 'No text layer found in the PDF (possibly scanned).'
    result.findings = [Finding('REVIEW', 'EXT-00',
                               'Could not extract quotation data from this PDF. A person must review the original document.',
                               snippet)]
    result.decision = 'Needs a person to check'


def ensure_seed(store: Store, request: dict, data_dir: Path) -> None:
    """Load the ten supplied sample packs once, so the dashboard starts with real records."""
    if store.get_meta('seeded') or store.count():
        return
    for pdf in sorted(Path(data_dir).glob('supplier-pack-*.pdf')):
        process_upload(store, request, pdf.name, pdf.read_bytes(), source='sample', actor='system')
    store.set_meta('seeded', '1')


def passed_rule_labels(result: dict) -> list[tuple[str, bool]]:
    """[(label, passed)] for every rule group."""
    failing = {f['rule'].split('-')[0] for f in result['findings']}
    if 'EXT' in failing or 'REQ' in failing:  # extraction/matching problems mean nothing can be claimed as passed
        return [(label, False) for _, label in RULE_GROUPS]
    return [(label, prefix not in failing) for prefix, label in RULE_GROUPS]


def limit_details(result: dict, request: dict) -> list[str]:
    """How far each violated limit was exceeded."""
    out = []
    req = request.get(result.get('item_code'))
    for f in result['findings']:
        r = f['rule']
        if r in ('PRICE-01', 'PRICE-02') and req and result.get('unit_price') is not None:
            mx, p = req['max_price'], result['unit_price']
            out.append(f"Quoted BDT {p:,.2f} vs PR maximum BDT {mx:,.2f} — over by BDT {p - mx:,.2f} ({(p - mx) / mx * 100:.2f}%). "
                       f"Highest price allowed with the 3% tolerance: BDT {mx * 1.03:,.2f}.")
        elif r == 'QTY-01' and req and result.get('quantity') is not None:
            q = req['quantity']
            out.append(f"Requested {q:,}; quoted {result['quantity']:,} — variance {abs(result['quantity'] - q) / q * 100:.1f}% (limit 5%).")
        elif r == 'PAY-02' and result.get('advance_pct') is not None:
            out.append(f"Advance {result['advance_pct']:g}% vs limit 20% — over by {result['advance_pct'] - 20:g} percentage points.")
        elif r == 'DEL-05' and result.get('delivery_days') is not None:
            out.append(f"Delivery {result['delivery_days']} days vs limit 45 days — over by {result['delivery_days'] - 45} days.")
        elif r == 'DEL-03' and result.get('penalty_pct_week') is not None:
            out.append(f"Penalty {result['penalty_pct_week']:g}% per week vs required minimum 0.5%.")
    return out
