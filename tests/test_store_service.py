import sys
from pathlib import Path
import fitz
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pipeline import load_request
from src.service import ensure_seed, process_upload
from src.store import Store

DATA = Path(__file__).resolve().parents[1] / 'data'
STATUS = {1: 'Approved', 2: 'Approved', 3: 'Rejected', 4: 'Human Review', 5: 'Rejected', 6: 'Rejected', 7: 'Human Review', 8: 'Rejected', 9: 'Human Review', 10: 'Rejected'}

@pytest.fixture
def env(tmp_path):
    store = Store(tmp_path / 'storage'); req = load_request(DATA / 'purchase-request.csv')
    ensure_seed(store, req, DATA)
    return store, req

def by_name(store):
    return {d['file_name']: d for d in store.list_documents()}

def make_pdf(text: str) -> bytes:
    doc = fitz.open(); page = doc.new_page()
    if text: page.insert_text((72, 72), text)
    return doc.tobytes()

def test_seed_creates_ten_separate_records(env):
    store, _ = env
    docs = by_name(store)
    assert len(docs) == 10
    for n, status in STATUS.items():
        assert docs[f'supplier-pack-{n:02d}.pdf']['status'] == status

def test_seed_runs_once(env):
    store, req = env
    ensure_seed(store, req, DATA)
    assert store.count() == 10

def test_duplicate_pdf_is_detected(env):
    store, req = env
    r = process_upload(store, req, 'renamed-copy.pdf', (DATA / 'supplier-pack-01.pdf').read_bytes())
    assert r['outcome'] == 'duplicate' and store.count() == 10

def test_bulk_failure_does_not_block_others(env):
    store, req = env
    outs = [process_upload(store, req, 'broken.pdf', b'not a pdf'),
            process_upload(store, req, 'broken2.pdf', b'%PDF-1.4 garbage'),
            process_upload(store, req, 'ok.pdf', make_pdf('Hello world'))]
    assert [o['outcome'] for o in outs] == ['failed', 'failed', 'processed']
    assert store.count() == 11

def test_unreadable_pdf_goes_to_human_review_not_guessed(env):
    store, req = env
    for name, text in [('blank.pdf', ''), ('other.pdf', 'Invoice for lunch')]:
        out = process_upload(store, req, name, make_pdf(text))
        d = by_name(store)[name]
        assert out['outcome'] == 'processed'
        assert d['status'] == 'Human Review' and d['result']['findings'][0]['rule'] == 'EXT-00'
        assert d['result']['findings'][0]['evidence']

def test_every_finding_has_rule_id_and_evidence(env):
    store, _ = env
    for d in store.list_documents():
        for f in d['result']['findings']:
            assert f['rule'] and f['evidence']

def test_human_review_is_stored_separately_and_ai_decision_unchanged(env):
    store, _ = env
    d = by_name(store)['supplier-pack-04.pdf']
    store.add_review(d['id'], 'Rahim', 'Approve', 'Within tolerance; accepted')
    d2 = by_name(store)['supplier-pack-04.pdf']
    assert d2['ai_decision'] == 'Needs a person to check'
    assert d2['status'] == 'Approved' and d2['status_source'] == 'Human review'
    assert d2['reviews'][0]['reviewer'] == 'Rahim' and d2['reviews'][0]['created_at']
    assert any(x['action'] == 'HUMAN_REVIEW' for x in store.audit_log(d['id']))

def test_request_more_information_keeps_document_in_queue(env):
    store, _ = env
    d = by_name(store)['supplier-pack-07.pdf']
    store.add_review(d['id'], 'Rahim', 'Request More Information', 'Confirm quantity')
    d2 = by_name(store)['supplier-pack-07.pdf']
    assert d2['status'] == 'Human Review' and d2['status_source'] == 'Info requested'

def test_review_not_allowed_on_ai_approved_or_rejected(env):
    store, _ = env
    for n in ('supplier-pack-01.pdf', 'supplier-pack-03.pdf'):
        with pytest.raises(ValueError):
            store.add_review(by_name(store)[n]['id'], 'Rahim', 'Approve', '')

def test_admin_override_is_audited_and_keeps_ai_decision(env):
    store, _ = env
    d = by_name(store)['supplier-pack-03.pdf']
    with pytest.raises(ValueError):
        store.add_override(d['id'], 'Admin', 'Approved', '   ')
    store.add_override(d['id'], 'Admin', 'Approved', 'Price renegotiated by phone')
    d2 = by_name(store)['supplier-pack-03.pdf']
    assert d2['ai_decision'] == 'Reject' and d2['status'] == 'Approved' and d2['status_source'] == 'Admin override'
    assert any(x['action'] == 'ADMIN_OVERRIDE' and 'Price renegotiated' in x['details'] for x in store.audit_log(d['id']))
