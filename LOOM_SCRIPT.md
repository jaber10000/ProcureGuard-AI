# Loom walkthrough script (target: 3–4 minutes)

## 0:00–0:30 — Problem
“Hi, I’m presenting ProcureGuard AI, a supplier quotation checker built for the BIAI Round 2 Task 1. Procurement teams need to compare supplier quotations with a purchase request and company rules. A wrong approval can create financial and compliance risk, so the system must not guess.”

## 0:30–1:15 — Architecture
“I built a fixed, auditable pipeline rather than a free-running agent. First, PyMuPDF extracts text from the supplied PDFs. Next, a structured parser extracts the quote fields. Then the engine compares item, quantity and price against the purchase request, checks the company rules, and aggregates the findings. Every finding has a rule ID, reason and source evidence. Reject takes priority over human review; a document is approved only when no configured rule is triggered.”

## 1:15–2:45 — Live demo
“Here is the dashboard with all ten supplier packs. We have two approvals, five rejections and three cases for a person to check. Let me open a few examples. Pack 03 is rejected because its unit price is BDT 229, above the 3% tolerance against the BDT 210 maximum. Pack 06 is rejected because it has no late-delivery penalty clause. Pack 09 is sent to a person because the payment window is ambiguous and the line arithmetic does not match. Pack 01 is approved because all configured checks pass. Notice that each result shows the exact extracted evidence.”

## 2:45–3:30 — Testing and honest limitations
“I ran the automated test suite against all ten supplied sample PDFs and all ten expected labels matched. This is agreement on this small sample, not a claim of production accuracy. The parser is tailored to the supplied text-based PDF layout; scanned documents and unfamiliar layouts need OCR and confidence checks. Ambiguous terms are routed to a person.”

## 3:30–4:00 — Next steps
“Next I would add OCR, support multiple line items and more supplier layouts, add a human correction and audit trail, and evaluate on a larger labelled dataset. If an LLM extractor is introduced, it would return schema-validated fields only; the deterministic policy engine would still make the final decision. Thank you.”

## Recording checklist
- Show the overview dashboard and the 2 / 5 / 3 outcome split.
- Open one Approve, one Reject, and one Human Review example.
- Show at least one exact evidence quotation.
- Show `pytest -q` passing in the terminal.
- Keep the recording under five minutes.
