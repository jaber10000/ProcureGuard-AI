🛡️ ProcureGuard AI
Overview

ProcureGuard AI is a supplier quotation verification system that analyzes supplier PDF quotations and validates them against purchase requests and company procurement rules.

The system extracts information from supplier quotations, applies validation rules, and generates evidence-backed decisions:

✅ Approved
❌ Rejected
⚠️ Human Review
Features
PDF quotation processing
Automatic field extraction
Purchase Request comparison
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
Project Structure
Plain Text
procureguard/
│
├── app.py
├── requirements.txt
├── data/
├── storage/
├── src/
└── tests/
Installation
1. Clone the Repository
Shell
git clone https://github.com/jaber10000/ProcureGuard-AI.git
cd ProcureGuard-AI/procureguard
2. Create a Virtual Environment
Shell
python -m venv .venv
3. Activate the Virtual Environment
Windows
Shell
.venv\Scripts\activate
Linux/macOS
Shell
source .venv/bin/activate
4. Install Dependencies
Shell
pip install -r requirements.txt
Running the Application

Start the Streamlit application:

Shell
streamlit run app.py

After startup, open the URL shown in the terminal, usually:

Plain Text
http://localhost:8501
How It Works
Upload supplier quotation PDFs.
Extract supplier and quotation information.
Compare data with the purchase request.
Apply procurement validation rules.
Generate one of three outcomes:
Approved
Rejected
Human Review
Display evidence and audit history.
Limitations
Optimized for text-based PDFs.
Scanned PDFs require OCR support.
Limited support for complex multi-item quotations.
Unfamiliar document layouts may require additional parsing rules.
Future Improvements
OCR integration
Multiple line-item support
Additional supplier templates
Enhanced audit workflows
Larger evaluation datasets
Author

Md. Abdullah Al Jaber

GitHub: https://github.com/jaber10000/ProcureGuard-AI
