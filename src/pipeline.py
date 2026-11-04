from __future__ import annotations
import csv, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import fitz

@dataclass
class Finding:
    severity: str  # REJECT or REVIEW
    rule: str
    message: str
    evidence: str

@dataclass
class SupplierResult:
    file_name: str
    supplier: str
    quotation_no: str
    quote_date: str
    item_code: str
    description: str
    quantity: Optional[int]
    unit: str
    unit_price: Optional[float]
    line_amount: Optional[float]
    subtotal: Optional[float]
    vat_amount: Optional[float]
    total: Optional[float]
    tin: Optional[str]
    bin: Optional[str]
    advance_pct: Optional[float]
    payment_days_min: Optional[int]
    payment_days_max: Optional[int]
    delivery_days: Optional[int]
    penalty_pct_week: Optional[float]
    validity_days: Optional[int]
    decision: str
    findings: list[Finding]
    extracted_text: str

    def to_dict(self):
        d = asdict(self)
        d['findings'] = [asdict(x) for x in self.findings]
        return d

NUM = r"[\d,]+(?:\.\d+)?"

def _num(s: str) -> float:
    return float(s.replace(',', ''))

def extract_pdf(pdf_path: str | Path) -> tuple[dict, str]:
    """Fixed extraction stage for the supplied, text-based quotation PDFs."""
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]
    supplier = next((x for x in lines if not any(k in x.upper() for k in ["QUOTATION", "ITEM ", "TO ", "TERMS AND", "SUPPLIER TIN", "FOR "])), "")
    qno = re.search(r"Quotation no\.\s*([A-Z0-9-]+)", text, re.I)
    qdate = re.search(r"Date\s+(\d{4}-\d{2}-\d{2})", text, re.I)
    item = None
    item_pattern = re.compile(rf"(?m)^([A-E])\s+(.+?)\s+({NUM})\s+(metre|piece|cone)\s+({NUM})\s+({NUM})$", re.I|re.S)
    # PyMuPDF's text layer may put each table cell on a separate line.
    m = item_pattern.search(text)
    if m:
        item = {"item_code":m.group(1), "description":re.sub(r"\s+", " ", m.group(2)).strip(), "quantity":int(_num(m.group(3))), "unit":m.group(4).lower(), "unit_price":_num(m.group(5)), "line_amount":_num(m.group(6)), "item_evidence":re.sub(r"\s+", " ", m.group(0)).strip()}
    def clause(n: int, next_n: int) -> str:
        m = re.search(rf"{n}\.\s*[^\n.]+\.?(.+?)(?=\s*{next_n}\.\s*[A-Z]|\s*For\s+|$)", text, re.I|re.S)
        if m:
            # Preserve the clause label and sentence, compacting whitespace.
            start = re.search(rf"{n}\.\s*[A-Z][^\n]*", text, re.I)
            return re.sub(r"\s+", " ", (start.group(0) if start else "") + " " + m.group(1)).strip()
        return ""
    # More reliable section extraction using numbered term boundaries.
    terms = re.search(r"TERMS AND CONDITIONS(.*?)(?=\nFor [^\n]+\nAuthorised signatory|\Z)", text, re.I|re.S)
    term_text = terms.group(1) if terms else ""
    clauses = {}
    matches = list(re.finditer(r"(?m)^\s*(\d+)\.\s*(.*?)(?=^\s*\d+\.\s|\Z)", term_text, re.S))
    for mt in matches:
        clauses[int(mt.group(1))] = re.sub(r"\s+", " ", mt.group(0)).strip()
    # Identify clauses by their semantic heading, not by clause number: a missing
    # clause must not cause every later clause to be misclassified.
    by_heading = {}
    for clause_text in clauses.values():
        hm = re.match(r"\d+\.\s*(Payment|Delivery|Delay|Validity)\.", clause_text, re.I)
        if hm:
            by_heading[hm.group(1).lower()] = clause_text
    payment = by_heading.get('payment', '')
    delivery = by_heading.get('delivery', '')
    delay = by_heading.get('delay', '')
    validity = by_heading.get('validity', '')
    tinm = re.search(r"Supplier TIN:\s*([0-9]+)", text, re.I)
    binm = re.search(r"BIN:\s*([0-9-]+)", text, re.I)
    if not tinm:
        tinm = re.search(r"TIN:\s*([0-9]+)", text, re.I)
    # Financial summary
    def money(label):
        m = re.search(rf"(?<![A-Za-z]){label}(?![A-Za-z])\s+({NUM})", text, re.I)
        return _num(m.group(1)) if m else None
    subtotal = money("Subtotal")
    vat = money(r"VAT\s*15%")
    total = money(r"Total(?!\s*\()")
    # Payment extraction
    adv = None
    if re.search(r"No advance payment", payment, re.I): adv = 0.0
    else:
        am = re.search(rf"({NUM})\s*%\s*advance", payment, re.I)
        if am: adv = _num(am.group(1))
    day_nums = [int(x) for x in re.findall(r"(\d+)\s*days?", payment, re.I)]
    pmin = min(day_nums) if day_nums else None
    pmax = max(day_nums) if day_nums else None
    # Delivery in days or weeks from PO
    delivery_days = None
    dm = re.search(r"within\s+(\d+)\s*(days?|weeks?)", delivery, re.I)
    if dm: delivery_days = int(dm.group(1)) * (7 if dm.group(2).lower().startswith('week') else 1)
    # Penalty percent per week
    pen = re.search(rf"({NUM})\s*%[^.\n]*(?:per\s+week|each\s+(?:full\s+)?week)", delay, re.I)
    penalty = _num(pen.group(1)) if pen else None
    vm = re.search(r"valid for\s+(\d+)\s*days", validity, re.I)
    valid_days = int(vm.group(1)) if vm else None
    data = dict(supplier=supplier, quotation_no=qno.group(1) if qno else "", quote_date=qdate.group(1) if qdate else "", item=item,
                tin=tinm.group(1) if tinm else None, bin=binm.group(1) if binm else None,
                payment=payment, delivery=delivery, delay=delay, validity=validity,
                delay_absence_evidence=" | ".join(x for x in [by_heading.get('delivery',''), by_heading.get('validity','')] if x),
                advance_pct=adv, payment_days_min=pmin, payment_days_max=pmax,
                delivery_days=delivery_days, penalty_pct_week=penalty, validity_days=valid_days,
                subtotal=subtotal, vat_amount=vat, total=total,
                vat_evidence=next((x for x in lines if re.search(r"VAT\s*15%", x, re.I)), ""),
                subtotal_evidence=next((x for x in lines if re.search(r"Subtotal", x, re.I)), ""),
                total_evidence=next((x for x in lines if re.search(r"Total", x, re.I)), ""))
    return data, text

def load_request(csv_path: str | Path) -> dict:
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return {r['Item']: {**r, 'quantity':int(r['Quantity requested']), 'max_price':float(r['Maximum unit price (BDT)'])} for r in rows}

def validate(data: dict, request: dict, file_name: str, text: str) -> SupplierResult:
    findings: list[Finding] = []
    item = data.get('item') or {}
    def reject(rule, msg, evidence): findings.append(Finding('REJECT', rule, msg, evidence or 'Evidence not found in document.'))
    def review(rule, msg, evidence): findings.append(Finding('REVIEW', rule, msg, evidence or 'Required information could not be extracted reliably.'))
    code = item.get('item_code', '')
    req = request.get(code)
    if not req: review('REQ-01', 'Could not match the quoted item to the purchase request.', item.get('item_evidence',''))
    if not item:
        review('EXT-01', 'Could not reliably extract the quotation line item.', '')
    else:
        if req:
            max_price = req['max_price']; price = item['unit_price']; qty = item['quantity']
            if price > max_price * 1.03 + 1e-9:
                reject('PRICE-01', f"Unit price BDT {price:,.2f} is more than 3% above the PR maximum BDT {max_price:,.2f}.", item['item_evidence'])
            elif price > max_price + 1e-9:
                review('PRICE-02', f"Unit price BDT {price:,.2f} is above the PR maximum BDT {max_price:,.2f}, but within 3%.", item['item_evidence'])
            diff = abs(qty-req['quantity'])/req['quantity']*100
            if diff > 5:
                review('QTY-01', f"Quoted quantity differs from requested quantity by {diff:.1f}% (requested {req['quantity']:,}; quoted {qty:,}).", item['item_evidence'])
        if abs(item['quantity']*item['unit_price']-item['line_amount']) > 0.02:
            review('MATH-01', 'Quantity multiplied by unit price does not match the quoted line amount.', item['item_evidence'])
    if not data.get('tin'): reject('TAX-01', 'Supplier TIN is missing.', 'Supplier registration details available on request.' if 'available on request' in text else '')
    if not data.get('bin'): reject('TAX-02', 'Supplier BIN is missing.', 'Supplier registration details available on request.' if 'available on request' in text else '')
    if data.get('advance_pct') is None:
        review('PAY-01', 'Advance payment terms could not be determined.', data.get('payment',''))
    elif data['advance_pct'] > 20:
        reject('PAY-02', f"Advance payment {data['advance_pct']:g}% exceeds the 20% maximum.", data.get('payment',''))
    if data.get('payment_days_min') is None or data.get('payment_days_max') is None or re.search(r"as agreed|subject to|to be agreed|mutual agreement", data.get('payment',''), re.I):
        review('PAY-03', 'Payment timing is unclear; a person must confirm the agreed payment date.', data.get('payment',''))
    elif data['payment_days_min'] < 30 or data['payment_days_max'] > 60:
        review('PAY-04', f"Payment window ({data['payment_days_min']}–{data['payment_days_max']} days) is outside the allowed 30–60 days after delivery.", data.get('payment',''))
    if not data.get('delay'):
        reject('DEL-01', 'No late-delivery penalty clause was found between the delivery and validity terms.', data.get('delay_absence_evidence') or 'No delay clause text was extracted from the contract.')
    elif data.get('penalty_pct_week') is None:
        review('DEL-02', 'Late-delivery penalty rate could not be verified.', data.get('delay',''))
    elif data['penalty_pct_week'] < 0.5:
        reject('DEL-03', f"Late-delivery penalty {data['penalty_pct_week']:g}% per week is below the required 0.5%.", data.get('delay',''))
    if data.get('delivery_days') is None:
        review('DEL-04', 'Delivery timing could not be determined.', data.get('delivery',''))
    elif data['delivery_days'] > 45:
        reject('DEL-05', f"Delivery in {data['delivery_days']} days exceeds the 45-day maximum.", data.get('delivery',''))
    elif data['delivery_days'] >= 31:
        review('DEL-06', f"Delivery in {data['delivery_days']} days falls in the 31–45 day review band.", data.get('delivery',''))
    if data.get('validity_days') is None:
        review('QUO-01', 'Quotation validity could not be verified.', data.get('validity',''))
    elif data['validity_days'] < 30:
        review('QUO-02', f"Quotation is valid for only {data['validity_days']} days; minimum is 30 days.", data.get('validity',''))
    if data.get('vat_amount') is None:
        review('VAT-01', 'VAT is not shown separately at 15%.', data.get('vat_evidence') or data.get('total_evidence',''))
    elif data.get('subtotal') is not None:
        expected_vat = data['subtotal'] * .15
        if abs(data['vat_amount']-expected_vat) > max(.02, expected_vat*.00001):
            review('VAT-02', f"VAT amount does not equal 15% of subtotal (expected BDT {expected_vat:,.2f}).", data.get('vat_evidence',''))
    if data.get('subtotal') is not None and data.get('vat_amount') is not None and data.get('total') is not None:
        if abs(data['subtotal']+data['vat_amount']-data['total']) > .02:
            review('MATH-02', 'Subtotal plus VAT does not equal the stated total.', f"{data.get('subtotal_evidence','')} | {data.get('vat_evidence','')} | {data.get('total_evidence','')}")
    elif data.get('subtotal') is None or data.get('total') is None:
        review('MATH-03', 'Could not verify the quotation subtotal and total.', '')
    if any(x.severity=='REJECT' for x in findings): decision='Reject'
    elif findings: decision='Needs a person to check'
    else: decision='Approve'
    return SupplierResult(file_name, data.get('supplier','Unknown supplier'), data.get('quotation_no',''), data.get('quote_date',''),
        code, item.get('description',''), item.get('quantity'), item.get('unit',''), item.get('unit_price'), item.get('line_amount'),
        data.get('subtotal'), data.get('vat_amount'), data.get('total'), data.get('tin'), data.get('bin'), data.get('advance_pct'),
        data.get('payment_days_min'), data.get('payment_days_max'), data.get('delivery_days'), data.get('penalty_pct_week'),
        data.get('validity_days'), decision, findings, text)

def run_pipeline(pdf_path: str | Path, request: dict) -> SupplierResult:
    extracted, text = extract_pdf(pdf_path)
    return validate(extracted, request, Path(pdf_path).name, text)

def run_folder(data_dir: str | Path) -> list[SupplierResult]:
    data_dir=Path(data_dir); request=load_request(data_dir/'purchase-request.csv')
    return [run_pipeline(p, request) for p in sorted(data_dir.glob('supplier-pack-*.pdf'))]
