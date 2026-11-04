ProcureGuard AI
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
git clone https://github.com/jaber10000/ProcureGuard-AI
cd procureguard
 
pip install -r requirements.txt
 
streamlit run app.py
Author

Abdullah Al Jaber
