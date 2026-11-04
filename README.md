# ProcureGuard AI

Evidence-based supplier quotation and contract checker built for the BIAI AI Engineer Round 2 Task 1 sample pack.

## What it does

ProcureGuard reads the ten supplied PDF packs locally, extracts structured commercial fields, compares the quoted item against `purchase-request.csv`, applies the policy in `company-rules.md`, and returns **Approve**, **Reject**, or **Needs a person to check**. Each finding includes a rule ID, a reason, and the exact supporting text (or an explicit statement that a required clause was not found).

## Architecture: fixed, auditable steps

1. **Document ingestion:** PyMuPDF reads text from each supplied PDF.
2. **Structured extraction:** deterministic parsers identify supplier, quote number/date, line item, prices, tax IDs, payment, delivery, penalty and validity terms.
3. **PR comparison:** item code, requested quantity and maximum unit price are loaded from the supplied CSV.
4. **Policy validation:** explicit Python rules implement the supplied reject/review/approve thresholds.
5. **Decision aggregation:** any Reject finding wins; otherwise any Review finding yields human review; only a clean document is approved.
6. **Evidence and reporting:** UI displays the extracted fields and quoted evidence; results can be exported to CSV.

This version deliberately does **not** call an external LLM or send the fictional sample documents to a third party. The supplied files are text-based and consistently formatted, so deterministic extraction makes the prototype reproducible and avoids inventing fields. For scanned or materially different supplier layouts, OCR/layout-aware extraction should be added and uncertain fields must remain in human review.

## Workspace (sidebar navigation)

Dashboard Overview · Upload Documents · All Documents · Approved · Rejected · Human Review · Purchase Request · Reports & Analytics

- **Dashboard:** total / approved / rejected / human-review cards. Each card opens its list; recent documents open full details.
- **Upload:** bulk (up to 10 PDFs, drag & drop, progress) or single upload. Every PDF gets its own record, result and evidence.
- **Duplicates:** identical files (SHA-256) are detected and not processed twice.
- **Failure isolation:** a corrupt/unreadable file is reported as failed; the other files in the batch are still processed.
- **No guessing:** a PDF with no recognisable quotation data goes to Human Review (`EXT-00`), never to Approve/Reject.
- **Document detaProcureGuard AI
Overview

ProcureGuard AI is a supplier quotation verification system that analyzes supplier PDF quotations and validates them against purchase requests and company procurement rules. The system produces evidence-backed decisions: Approved, Rejected, or Human Review.

Features
PDF quotation processing
Automatic field extraction
Purchase request comparison
Rule-based validation engine
Evidence-backed decisions
Human review workflow
Audit trail tracking
Reports and CSV export
Technology Stack
Python
Streamlit
PyMuPDF (fitz)
Pandas
How It Works
Upload supplier quotation PDFs.
Extract information from documents.
Compare quotation details against purchase requests.
Apply company validation rules.
Generate Approved, Rejected, or Human Review decisions.
Display evidence and audit history.
Current Limitations
Optimized for text-based PDFs.
Scanned PDFs require OCR support.
Limited support for complex multi-item quotations.
Unfamiliar document layouts may require additional parsing rules.
Future Improvements
OCR integration
Multiple line-item support
Additional supplier templates
Enhanced audit and reviewer workflows
Larger-scale evaluation dataset support
Run Locally
Shell
git clone <repository-url>
cd procureguard
 
pip install -r requirements.txt
 
streamlit run app.py
Author

Abdullah Al Jabeil:** supplier info, quotation details, PR comparison, every rule with Rule ID + exact PDF evidence, how far limits were exceeded, original PDF preview, audit trail.
- **Human Review:** reviewer name, time, comment and decision (Approve / Reject / Request More Information) are saved in their own table, separate from the AI decision.
- **Admin override:** the AI decision is never modified. An admin override (mandatory reason) changes only the final status and is written to the audit log.
- **Reports:** status chart, rule-finding frequency, CSV export of documents and of the audit log.

Final status = admin override > latest human review > AI decision.

Data is stored in `storage/` (SQLite `procureguard.db` + uploaded PDFs). The ten sample packs are loaded once on first start. Delete `storage/` to reset. On hosts with an ephemeral disk (e.g. Streamlit Community Cloud) this data is lost on restart.

> Prototype note: “Signed in as” and “Role” in the sidebar are **not authentication**. Add real login/RBAC before production use.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (usually http://localhost:8501). Set `PROCUREGUARD_STORAGE=/some/path` to change where data is stored.

## Run without the web dashboard

```bash
python run.py
```

This prints every decision and writes `procureguard-results.csv`.

## Run tests

```bash
pytest -q
```

Covers the ten expected sample decisions, duplicate detection, failure isolation, no-guessing, separate human-review storage, admin-override audit, and UI smoke tests for every page.

## Policy implementation notes

- Unit price **more than** 3% above PR maximum: Reject; above maximum up to and including 3%: Review.
- Advance payment above 20%: Reject.
- Missing late-delivery penalty clause: Reject; penalty below 0.5% per week: Reject.
- Missing supplier TIN or BIN: Reject.
- Delivery over 45 days: Reject; 31–45 days: Review.
- Quantity variance over 5%, unclear/out-of-range payment, separately unstated/non-15% VAT, arithmetic mismatch, or validity under 30 days: Review.
- Reject takes precedence over Review if both apply.

## Known limitations

- The parser is tuned to the supplied, text-based PDF template; it is not a general-purpose OCR or document-understanding model.
- Dates such as “four weeks” are normalized to 28 days. The prototype does not calculate calendar delivery dates because the purchase-order issue date is not supplied.
- Payment wording is parsed conservatively. Ambiguous phrases are routed to a person rather than guessed.
- VAT-inclusive-only totals are flagged for review because VAT is not separately stated.
- This is a decision-support prototype, not legal/procurement approval software.

## Next steps

Add OCR with confidence thresholds, support multiple line items and document layouts, add human correction/feedback, create a larger labelled evaluation set, and integrate role-based approval/audit logging. An optional LLM extractor could be introduced behind a strict JSON schema, with confidence checks and the same deterministic validator; it must never make the final policy decision.

## Sample data

The `data/` directory contains only the sample files provided in the BIAI task pack. All entities are fictional.
