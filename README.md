# 🛡️ ProcureGuard AI
### Intelligent Supplier Quotation Verification & Procurement Compliance System

ProcureGuard AI is a Python-based supplier quotation verification system that extracts information from supplier PDF quotations, compares it against purchase requests, and validates it against predefined procurement rules.

The system generates transparent, evidence-backed decisions to help procurement teams review supplier quotations efficiently and consistently.

## ✨ Key Features

- **PDF Document Processing** – Upload and process supplier quotation PDFs.
- **Automatic Data Extraction** – Extract supplier details, item descriptions, quantities, prices, VAT, payment terms, delivery schedules, and other relevant information.
- **Purchase Request Comparison** – Compare extracted quotation data against predefined purchase request requirements.
- **Rule-Based Validation** – Apply procurement policies and compliance rules automatically.
- **Evidence-Based Decisions** – Display supporting document text for each validation result.
- **Decision Classification** – Categorize quotations into:
  - ✅ Approved
  - ❌ Rejected
  - ⚠️ Human Review
- **Human Review Workflow** – Allow uncertain cases to be reviewed by a human.
- **Audit Trail** – Track processing results and review activities.
- **Reports & CSV Export** – Export quotation analysis results for further review.

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| PyMuPDF (fitz) | PDF text extraction |
| Pandas | Data processing and analysis |
| SQLite / Local Storage | Application data and audit records |
| Pytest | Automated testing |

## 📁 Project Structure

```text
ProcureGuard-AI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── supplier_quotations/
│   ├── purchase-request.csv
│   └── company-rules.md
│
├── storage/
│   └── application records
│
├── src/
│   ├── pipeline.py
│   ├── extraction.py
│   ├── validation.py
│   └── decision_engine.py
│
└── tests/
    └── test_pipeline.py
```

*Note: The structure above describes the intended organization. Adjust filenames to match the actual repository.*

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jaber10000/ProcureGuard-AI.git
cd ProcureGuard-AI/procureguard
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal:

```text
http://localhost:8501
```

## 🔍 How It Works

ProcureGuard AI follows a structured document verification pipeline:

1. **Document Upload:** Upload one or multiple supplier quotation PDFs.
2. **Information Extraction:** Extract relevant supplier and quotation information from each PDF.
3. **Data Validation:** Check whether the extracted information is available and usable.
4. **Purchase Request Matching:** Compare item descriptions, quantities, and prices against the purchase request.
5. **Procurement Rule Checking:** Evaluate the quotation against company procurement policies.
6. **Decision Generation:** Generate an evidence-backed outcome for each quotation.
7. **Human Review:** Route uncertain cases for manual verification.
8. **Audit & Reporting:** Maintain review records and export results.

### Decision Outcomes

| Decision | Description |
|---|---|
| ✅ Approved | The quotation satisfies the applicable procurement requirements. |
| ❌ Rejected | One or more rejection conditions have been identified. |
| ⚠️ Human Review | The quotation contains uncertain or exceptional conditions requiring manual verification. |

## 🧪 Testing

Run the automated test suite using:

```bash
pytest -v
```

The tests are designed to verify the document-processing pipeline, decision classifications, and supporting evidence.

## ⚠️ Limitations

- Currently optimized for text-based PDF documents.
- Scanned PDFs require OCR integration.
- Complex multi-item quotation layouts may need additional parsing logic.
- Unfamiliar document formats may require new extraction patterns.
- Extraction accuracy depends on the structure and quality of the source documents.

## 🔮 Future Improvements

- OCR support for scanned documents.
- Improved extraction using document AI techniques.
- Support for complex multi-item quotations.
- Additional supplier document templates.
- Enhanced human review and approval workflows.
- More comprehensive audit logging.
- Expanded evaluation datasets and automated accuracy reporting.

## 👨‍💻 Author

**Md. Abdullah Al Jaber**

- GitHub: [@jaber10000](https://github.com/jaber10000)
- Project: [ProcureGuard AI](https://lbvuklvmbyf2appsecl5ueg.streamlit.app/)

---

*Built to make supplier quotation verification more transparent, consistent, and efficient.*
