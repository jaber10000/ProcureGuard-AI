# ProcureGuard AI — BIAI Round 2 Task 1

## What I built
A local, fixed-step supplier-document verification prototype. It reads the ten supplied text-based PDF quotations, extracts supplier and commercial terms, compares each line with the supplied purchase request, applies the company rules, and displays an evidence-backed decision: Approve, Reject, or Needs a person to check. The Streamlit dashboard includes extracted fields, rule IDs, supporting quotations, a full-text inspection view, and CSV export.

## How it works
PyMuPDF extracts PDF text. A deterministic parser structures the fields. Python validation rules compare item, quantity and price with the PR and check advance, payment timing, delivery, late penalty, TIN/BIN, VAT, arithmetic and quote validity. Decisions are aggregated conservatively: any Reject finding results in Reject; otherwise any Review finding results in human review; only documents with no findings are approved. No external AI API is called and no supplied data leaves the machine.

## Testing and results
The automated test suite runs against all ten provided PDFs and checks the expected labels and evidence presence for rejection findings. Run `pytest -q`. Expected sample outcomes: 2 Approve, 5 Reject, 3 Needs a person to check. The dashboard reports the exact agreement count at runtime. This score is agreement on the supplied ten examples, not a claim of general accuracy.

## What does not work well
The extractor is tuned to the supplied text-based PDF layout; scanned documents, unusual layouts, multiple line items, or low-quality OCR are not supported. The parser deliberately sends unclear terms to human review. Calendar delivery dates cannot be calculated because no PO issue date is provided. The current prototype does not use an LLM; it prioritizes reproducibility and auditable rules over generative extraction.

## What I would do next
Add OCR and extraction confidence thresholds, expand support for multiple line items and varied supplier templates, introduce a human correction/audit trail, evaluate on a larger labelled dataset, and optionally add a schema-constrained LLM extraction stage while keeping the final policy decision deterministic.
