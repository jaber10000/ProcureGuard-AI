"""ProcureGuard AI — supplier document verification workspace (Streamlit)."""
from __future__ import annotations
import base64, html, os, sys
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
sys.path.insert(0, str(ROOT))
from src.pipeline import load_request
from src.service import MAX_BULK, ensure_seed, limit_details, passed_rule_labels, process_upload
from src.store import Store

st.set_page_config(page_title='ProcureGuard AI', page_icon='🛡️', layout='wide', initial_sidebar_state='expanded')

PAGES = ['Dashboard Overview', 'Upload Documents', 'All Documents', 'Approved', 'Rejected', 'Human Review', 'Purchase Request', 'Reports & Analytics']
ICONS = {'Dashboard Overview': '', 'Upload Documents': '⬆', 'All Documents': '', 'Approved': '', 'Rejected': '',
         'Human Review': '', 'Purchase Request': '', 'Reports & Analytics': ''}
STATUS_CLASS = {'Approved': 'pg-pass', 'Rejected': 'pg-fail', 'Human Review': 'pg-warn'}
REVIEW_CHOICES = {'Approve this supplier': 'Approve', 'Reject this supplier': 'Reject', 'Request More Information': 'Request More Information'}

# ---------- visual system ----------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#061311; --line:#1b3b35; --muted:#8ca7a0; --text:#e8f3ef; }
html, body, [data-testid="stAppViewContainer"] { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:rgba(6,19,17,.92); }
[data-testid="stSidebar"] { background:#081714; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:4.2rem; padding-bottom:2rem; max-width:1500px; }
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display:none; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { gap:4px; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] { width:100%; background:transparent; border:1px solid transparent; border-radius:10px; padding:9px 12px; margin:0; transition:all .15s ease; cursor:pointer; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover { background:#10211e; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] { background:#123b34; border-color:#1aa991; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child { display:none; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] p { font-size:14px; font-weight:600; color:#b9d0ca; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p { color:#6de7d2; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; color:#f1faf7 !important; }
h1 { font-size:1.8rem !important; } h2 { font-size:1.2rem !important; } h3 { font-size:1rem !important; }
small, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#102522,#0b1b19); border:1px solid var(--line); border-radius:14px; padding:14px 16px; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:#10211e; border:1px solid var(--line); border-radius:9px 9px 0 0; color:#b9d0ca; padding:9px 18px; }
.stTabs [aria-selected="true"] { background:#123b34 !important; color:#6de7d2 !important; border-color:#1aa991 !important; }
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { background:#0e8878; color:white; border:1px solid #1db9a2; border-radius:10px; font-weight:600; }
.stButton button:hover, .stDownloadButton button:hover, [data-testid="stFormSubmitButton"] button:hover { background:#13a28e; color:white; border-color:#52e2c8; }
[data-testid="stExpander"] { background:#0b1b19; border:1px solid var(--line); border-radius:12px; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line) !important; border-radius:14px !important; background:linear-gradient(145deg,#0f2320,#0a1b18); }
[data-testid="stFileUploaderDropzone"] { background:#0b1b19; border:2px dashed #1f5a4f; border-radius:14px; }
.pg-live { color:#72e6d2; background:#10362f; border:1px solid #1b665a; padding:6px 11px; border-radius:30px; font-size:12px; display:inline-block; }
.pg-stat { background:linear-gradient(145deg,#102522,#0a1b18); border:1px solid var(--line); border-radius:14px; padding:18px 18px 12px; }
.pg-stat .lbl { color:#9bb8b0; font-size:12px; letter-spacing:.08em; font-weight:700; text-transform:uppercase; }
.pg-stat .num { font-family:'Space Grotesk'; font-size:40px; font-weight:700; line-height:1.15; }
.pg-card-title { font-family:'Space Grotesk'; font-weight:600; font-size:15px; margin-bottom:10px; color:#edf8f4; }
.pg-field { display:flex; justify-content:space-between; gap:12px; padding:9px 2px; border-bottom:1px solid #18342f; font-size:13px; }
.pg-field:last-child { border-bottom:0; }
.pg-field span:first-child { color:#91aaa3; }
.pg-field strong { color:#e9f7f2; text-align:right; word-break:break-word; }
.pg-pill { display:inline-block; border-radius:30px; padding:4px 10px; font-size:11px; font-weight:700; white-space:nowrap; }
.pg-pass { color:#65e2bd; background:#103b30; border:1px solid #1c6b53; }
.pg-fail { color:#ff8b8b; background:#401d22; border:1px solid #7b333b; }
.pg-warn { color:#ffd17a; background:#3a2d17; border:1px solid #715426; }
.pg-info { color:#9cc8ff; background:#16283f; border:1px solid #2c4b75; }
.pg-row { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.pg-sub { color:#8ca7a0; font-size:12px; margin:2px 0 8px; }
.pg-rule { padding:11px 12px; background:#0c201d; border:1px solid #1a3933; border-radius:10px; margin:8px 0; }
.pg-rule b { font-size:13px; } .pg-rule p { margin:5px 0 0; color:#a9c0b9; font-size:12.5px; }
.pg-evidence { background:#071513; border-left:3px solid #1aa991; border-radius:6px; padding:8px 10px; margin:6px 0 8px; font-family:ui-monospace,Menlo,monospace; font-size:12px; color:#cfe6e0; white-space:pre-wrap; word-break:break-word; }
.pg-pass-row { padding:7px 10px; border-bottom:1px solid #18342f; font-size:13px; color:#b9d0ca; }
.pg-pass-row.bad { color:#ffb4b4; }
.pg-tl { border-left:2px solid #1b665a; margin:6px 0 6px 6px; padding-left:15px; }
.pg-tl div { margin:0 0 12px; font-size:12px; color:#bad0ca; } .pg-tl b { color:#e9f7f2; display:block; margin-bottom:2px; }
</style>
""", unsafe_allow_html=True)

# ---------- helpers ----------
def esc(x) -> str:
    return '—' if x is None or x == '' else html.escape(str(x))

def pill(status: str) -> str:
    return f"<span class='pg-pill {STATUS_CLASS.get(status, 'pg-info')}'>{esc(status)}</span>"

def pack_label(name: str) -> str:
    return Path(name).stem.replace('-', ' ').replace('_', ' ').title()

def money(v) -> str:
    return '—' if v is None else f'BDT {v:,.2f}'

def field_rows(rows) -> str:
    return ''.join(f"<div class='pg-field'><span>{esc(k)}</span><strong>{esc(v)}</strong></div>" for k, v in rows)

def go(page: str, doc_id: int | None = None):
    st.session_state.nav = page
    st.session_state.selected_doc = doc_id

def clear_selection():
    st.session_state.selected_doc = None

def flash(kind: str, msg: str):
    st.session_state.flash = (kind, msg)

@st.cache_resource
def get_store() -> Store:
    return Store(os.environ.get('PROCUREGUARD_STORAGE', ROOT / 'storage'))

@st.cache_data
def get_request():
    return load_request(DATA / 'purchase-request.csv')

store = get_store()
request = get_request()
if not (DATA / 'purchase-request.csv').exists():
    st.error('data/purchase-request.csv is missing.'); st.stop()
ensure_seed(store, request, DATA)
docs = store.list_documents()
by_id = {d['id']: d for d in docs}
counts = Counter(d['status'] for d in docs)

ss = st.session_state
ss.setdefault('nav', PAGES[0]); ss.setdefault('selected_doc', None); ss.setdefault('uploader_n', 0)

def basis_text(d: dict) -> str:
    """Why this document has its current status (rule findings, reviewer or admin)."""
    if d['status_source'] == 'Admin override':
        o = d['overrides'][-1]; return f"Admin override by {o['admin']}: {o['reason']}"
    if d['status_source'] in ('Human review', 'Info requested'):
        r = d['reviews'][-1]; return f"Reviewer {r['reviewer']} — {r['decision']}: {r['comment'] or 'no comment'}"
    return ' '.join(f['message'] for f in d['result']['findings']) or 'All configured rules passed.'

def pdf_preview(d: dict, height: int = 650):
    p = store.pdf_path(d['sha256'])

    if not p.exists():
        st.warning("Original PDF file not found in storage.")
        return

    pdf_bytes = p.read_bytes()
    b64 = base64.b64encode(pdf_bytes).decode()

    st.markdown(
        f"""
        <embed
            src="data:application/pdf;base64,{b64}"
            width="100%"
            height="{height}"
            type="application/pdf">
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        "⇩ Download original PDF",
        pdf_bytes,
        d["file_name"],
        "application/pdf",
        key=f"dl_{d['id']}_{height}"
    )

    st.success("PDF file found successfully.")

# ---------- forms ----------
def review_form(d: dict, key: str):
    st.markdown("**Reviewer Decision**")
    reviewer = ss.get('user_name', '').strip()
    if not reviewer:
        st.warning('Enter your name in the sidebar (“Signed in as”) so the decision can be recorded against you.')
    with st.form(f'review_{key}_{d["id"]}'):
        choice = st.radio('Reviewer Decision', list(REVIEW_CHOICES), label_visibility='collapsed')
        comment = st.text_area('Comment', placeholder='Reason for the decision (required for Reject / Request More Information)')
        if st.form_submit_button('Submit Review Decision'):
            decision = REVIEW_CHOICES[choice]
            if not reviewer:
                st.error('Reviewer name is required.')
            elif decision != 'Approve' and not comment.strip():
                st.error('Please add a comment for this decision.')
            else:
                store.add_review(d['id'], reviewer, decision, comment.strip())
                flash('success', f"Decision saved for {d['result']['supplier']}: {choice}.")
                st.rerun()

def override_form(d: dict):
    admin = ss.get('user_name', '').strip()
    with st.expander('🔐 Admin override (audited)'):
        st.caption('The original AI decision is kept on record. An override only changes the final status and is written to the audit log. '
                   'Prototype note: the Role selector is not real authentication.')
        if ss.get('role') != 'Admin':
            st.info('Switch Role to “Admin” in the sidebar to override.'); return
        if not admin:
            st.warning('Enter your name in the sidebar first.'); return
        with st.form(f'override_{d["id"]}'):
            decision = st.radio('Final status', ['Approved', 'Rejected'], horizontal=True)
            reason = st.text_area('Reason (mandatory)')
            if st.form_submit_button('Apply override'):
                if not reason.strip():
                    st.error('A reason is mandatory.')
                else:
                    store.add_override(d['id'], admin, decision, reason)
                    flash('success', f'Override recorded: final status set to {decision}.')
                    st.rerun()

# ---------- document detail ----------
def show_detail(d: dict):
    r = d['result']
    st.button('← Back', key=f"back_{d['id']}", on_click=clear_selection)
    st.markdown(f"<div class='pg-row'><h1 style='margin:0'>{esc(r['supplier'])}</h1>{pill(d['status'])}</div>"
                f"<div class='pg-sub'>{esc(pack_label(d['file_name']))} · {esc(d['file_name'])} · Quotation {esc(r['quotation_no'])} · uploaded {esc(d['uploaded_at'])} · source: {esc(d['source'])}</div>",
                unsafe_allow_html=True)

    # Final decision: AI, human and admin kept separate
    ai_cls = {'Approve': 'pg-pass', 'Reject': 'pg-fail'}.get(d['ai_decision'], 'pg-warn')
    rev = d['reviews'][-1] if d['reviews'] else None
    ovr = d['overrides'][-1] if d['overrides'] else None
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='pg-stat'><div class='lbl'>AI decision (locked)</div><div style='margin-top:8px'><span class='pg-pill {ai_cls}'>{esc(d['ai_decision'])}</span></div><div class='pg-sub'>{len(r['findings'])} finding(s)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='pg-stat'><div class='lbl'>Human review</div><div style='margin-top:8px'>{esc(rev['decision']) if rev else 'Not reviewed'}</div><div class='pg-sub'>{esc(rev['reviewer'] + ' · ' + rev['created_at']) if rev else 'Separate record'}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='pg-stat'><div class='lbl'>Admin override</div><div style='margin-top:8px'>{esc(ovr['decision']) if ovr else 'None'}</div><div class='pg-sub'>{esc(ovr['admin'] + ' · ' + ovr['created_at']) if ovr else 'Audit-logged if used'}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='pg-stat'><div class='lbl'>Final decision</div><div style='margin-top:8px'>{pill(d['status'])}</div><div class='pg-sub'>Decided by: {esc(d['status_source'])}</div></div>", unsafe_allow_html=True)
    if rev and rev['comment']:
        st.caption(f"Reviewer comment: {rev['comment']}")
    if ovr:
        st.caption(f"Override reason: {ovr['reason']}")
    st.write('')

    a, b = st.columns(2, gap='medium')
    with a:
        with st.container(border=True):
            st.markdown("<div class='pg-card-title'>Supplier Information</div>" + field_rows([('Supplier', r['supplier']), ('TIN', r['tin'] or 'Not found'), ('BIN', r['bin'] or 'Not found'), ('Quotation date', r['quote_date'])]), unsafe_allow_html=True)
    with b:
        with st.container(border=True):
            st.markdown("<div class='pg-card-title'>Quotation Details</div>" + field_rows([
                ('Quotation number', r['quotation_no']), ('Item', f"{r['item_code']} · {r['description']}" if r['item_code'] else None),
                ('Quantity', f"{r['quantity']:,} {r['unit']}" if r['quantity'] is not None else None), ('Unit price', money(r['unit_price']) if r['unit_price'] is not None else None),
                ('Line amount', money(r['line_amount']) if r['line_amount'] is not None else None), ('Subtotal', money(r['subtotal']) if r['subtotal'] is not None else None),
                ('VAT 15%', money(r['vat_amount']) if r['vat_amount'] is not None else None), ('Total', money(r['total']) if r['total'] is not None else None),
                ('Advance payment', f"{r['advance_pct']:g}%" if r['advance_pct'] is not None else None),
                ('Payment window', (f"{r['payment_days_min']} days" if r['payment_days_min'] == r['payment_days_max'] else f"{r['payment_days_min']}–{r['payment_days_max']} days") if r['payment_days_min'] is not None else None),
                ('Delivery', f"{r['delivery_days']} days" if r['delivery_days'] is not None else None),
                ('Late penalty', f"{r['penalty_pct_week']:g}% / week" if r['penalty_pct_week'] is not None else None),
                ('Quote validity', f"{r['validity_days']} days" if r['validity_days'] is not None else None)]), unsafe_allow_html=True)

    st.subheader('Purchase Request Comparison')
    req = request.get(r['item_code'])
    if req:
        qv = (r['quantity'] - req['quantity']) / req['quantity'] * 100 if r['quantity'] is not None else None
        pv = (r['unit_price'] - req['max_price']) / req['max_price'] * 100 if r['unit_price'] is not None else None
        st.dataframe(pd.DataFrame([
            {'Check': 'Quantity', 'Purchase request': f"{req['quantity']:,}", 'Quoted': f"{r['quantity']:,}" if r['quantity'] is not None else 'Not found', 'Variance': f'{qv:+.1f}%' if qv is not None else '—', 'Limit': '±5%'},
            {'Check': 'Unit price (BDT)', 'Purchase request': f"{req['max_price']:,.2f} (max)", 'Quoted': f"{r['unit_price']:,.2f}" if r['unit_price'] is not None else 'Not found', 'Variance': f'{pv:+.2f}%' if pv is not None else '—', 'Limit': f"+3% (≤ {req['max_price'] * 1.03:,.2f})"}]),
            hide_index=True, use_container_width=True)
    else:
        st.warning('The quoted item could not be matched to a purchase request line. Nothing was assumed.')

    st.subheader('Rule Results & Exact PDF Evidence')
    if not r['findings']:
        st.success('All rules passed.')
    for f in r['findings']:
        cls = 'pg-fail' if f['severity'] == 'REJECT' else 'pg-warn'
        st.markdown(f"<div class='pg-rule'><span class='pg-pill {cls}'>{esc(f['severity'])}</span> &nbsp;<b>Rule ID: {esc(f['rule'])}</b><p>{esc(f['message'])}</p><div class='pg-evidence'>“{esc(f['evidence'])}”</div></div>", unsafe_allow_html=True)
    for line in limit_details(r, request):
        st.caption('Limit check: ' + line)
    with st.expander('All rule groups', expanded=not r['findings']):
        st.markdown(''.join(f"<div class='pg-pass-row{'' if ok else ' bad'}'>{'✓' if ok else '✗'}&nbsp; {esc(label)}</div>" for label, ok in passed_rule_labels(r)), unsafe_allow_html=True)

    if d['status'] == 'Human Review' and d['ai_decision'] == 'Needs a person to check':
        st.subheader('Reviewer Decision')
        review_form(d, 'detail')
    override_form(d)

    t1, t2, t3 = st.tabs(['Original PDF', 'Extracted text', 'Audit trail'])
    with t1: pdf_preview(d)
    with t2: st.text_area('Extracted PDF text', r['extracted_text'], height=340, disabled=True)
    with t3:
        log = store.audit_log(d['id'])
        st.markdown("<div class='pg-tl'>" + ''.join(f"<div><b>{esc(x['action'])} · {esc(x['actor'])}</b>{esc(x['ts'])}<br>{esc(x['details'])}</div>" for x in log) + "</div>", unsafe_allow_html=True)

# ---------- pages ----------
def stat_card(col, label: str, value: int, color: str, hint: str, page: str | None):
    with col:
        st.markdown(f"<div class='pg-stat'><div class='lbl'>{label}</div><div class='num' style='color:{color}'>{value}</div><div class='pg-sub'>{hint}</div></div>", unsafe_allow_html=True)
        if page:
            st.button('View details →', key=f'stat_{label}', on_click=go, args=(page,), use_container_width=True)

def page_dashboard():
    st.markdown("<div class='pg-live'>● System Ready</div>", unsafe_allow_html=True)
    st.title('Supplier Document Verification')
    c = st.columns(4)
    stat_card(c[0], 'Total documents', len(docs), '#e9f7f2', 'All processed records', 'All Documents')
    stat_card(c[1], 'Approved', counts['Approved'], '#65e2bd', 'Click to view details', 'Approved')
    stat_card(c[2], 'Rejected', counts['Rejected'], '#ff8b8b', 'Click to view details', 'Rejected')
    stat_card(c[3], 'Human Review', counts['Human Review'], '#ffd17a', 'Click to review', 'Human Review')
    st.write('')
    st.subheader('Recent Documents')
    st.caption('Latest processed supplier quotations')
    if not docs:
        st.info('No documents yet. Use “Upload Documents” to add supplier PDFs.')
    for d in docs[:6]:
        with st.container(border=True):
            a, b, c2 = st.columns([3, 1.3, 1])
            a.markdown(f"**{esc(d['result']['supplier'])}**<div class='pg-sub'>{esc(pack_label(d['file_name']))} · {esc(d['uploaded_at'])}</div>", unsafe_allow_html=True)
            b.markdown(pill(d['status']), unsafe_allow_html=True)
            c2.button('Open', key=f"recent_{d['id']}", on_click=go, args=('All Documents', d['id']), use_container_width=True)

def run_batch(files) -> list[dict]:
    results, bar, msg = [], st.progress(0.0), st.empty()
    for i, f in enumerate(files):
        msg.caption(f'Processing {f.name} ({i + 1}/{len(files)})…')
        results.append(process_upload(store, request, f.name, f.getvalue(), actor=ss.get('user_name', '').strip() or 'uploader'))
        bar.progress((i + 1) / len(files))
    msg.empty(); bar.empty()
    return results

def upload_results(results: list[dict]):
    st.subheader('Upload result')
    ok = sum(r['outcome'] == 'processed' for r in results)
    dup = sum(r['outcome'] == 'duplicate' for r in results)
    bad = sum(r['outcome'] == 'failed' for r in results)
    st.caption(f'{ok} processed · {dup} duplicate · {bad} failed. Each processed PDF has its own record, result and evidence.')
    for i, r in enumerate(results):
        icon = {'processed': '✅', 'duplicate': '⚠️', 'failed': '❌'}[r['outcome']]
        d = by_id.get(r['doc_id'])
        with st.container(border=True):
            a, b, c = st.columns([3, 2, 1])
            a.markdown(f"{icon} **{esc(r['file_name'])}**<div class='pg-sub'>{esc(r['message'])}</div>", unsafe_allow_html=True)
            if d and r['outcome'] == 'processed':
                b.markdown(f"{pill(d['status'])}<div class='pg-sub'>{len(d['result']['findings'])} finding(s)</div>", unsafe_allow_html=True)
            if d:
                c.button('View result', key=f'ur_{i}_{d["id"]}', on_click=go, args=('All Documents', d['id']), use_container_width=True)

def page_upload():
    st.title('Upload Documents')
    st.caption('Each PDF is processed independently. Identical files (same SHA-256) are detected as duplicates; one failing file never stops the others.')
    tab_a, tab_b = st.tabs(['Option A — Bulk Upload', 'Option B — Single Upload'])
    n = ss.uploader_n
    with tab_a:
        files = st.file_uploader(f'Drag & drop up to {MAX_BULK} PDFs, or browse', type=['pdf'], accept_multiple_files=True, key=f'bulk_{n}')
        if len(files) > MAX_BULK:
            st.error(f'Please select at most {MAX_BULK} PDFs at a time ({len(files)} selected).')
        elif files and st.button(f'Process {len(files)} document(s)', key='go_bulk', type='primary'):
            ss.last_upload = run_batch(files); ss.uploader_n += 1; st.rerun()
    with tab_b:
        one = st.file_uploader('Select one PDF', type=['pdf'], key=f'single_{n}')
        if one and st.button('Upload & process', key='go_single', type='primary'):
            ss.last_upload = run_batch([one]); ss.uploader_n += 1; st.rerun()
    if ss.get('last_upload'):
        upload_results(ss.last_upload)

def apply_open_doc():
    """Return True when a document detail view was shown."""
    if ss.selected_doc is not None:
        d = by_id.get(ss.selected_doc)
        if d:
            show_detail(d); return True
        ss.selected_doc = None
    return False

def page_all():
    if apply_open_doc(): return
    st.title('All Documents')
    c1, c2 = st.columns([1, 2])
    status = c1.selectbox('Status', ['All', 'Approved', 'Rejected', 'Human Review'])
    q = c2.text_input('Search supplier, file or quotation number')
    rows = [d for d in docs if (status == 'All' or d['status'] == status) and (not q or q.lower() in f"{d['result']['supplier']} {d['file_name']} {d['result']['quotation_no']}".lower())]
    if not rows:
        st.info('No documents match.'); return
    df = pd.DataFrame([{'File': d['file_name'], 'Supplier': d['result']['supplier'], 'Quotation': d['result']['quotation_no'] or '—', 'Item': d['result']['item_code'] or '—',
                        'Unit price (BDT)': d['result']['unit_price'], 'AI decision': d['ai_decision'], 'Final status': d['status'], 'Decided by': d['status_source'], 'Rules hit': '; '.join(f['rule'] for f in d['result']['findings']) or '—'} for d in rows])
    st.caption('Select a row to open its full details.')
    ev = st.dataframe(df, hide_index=True, use_container_width=True, on_select='rerun', selection_mode='single-row')
    if ev.selection.rows:
        picked = rows[ev.selection.rows[0]]
        st.button(f"Open details: {picked['result']['supplier']} →", on_click=go, args=('All Documents', picked['id']), type='primary')

def page_status(status: str):
    if apply_open_doc(): return
    rows = [d for d in docs if d['status'] == status]
    st.title(f'{status} Documents')
    st.caption(f'{len(rows)} Document{"s" if len(rows) != 1 else ""}')
    if not rows:
        st.info(f'No {status.lower()} documents.'); return
    cols = st.columns(2, gap='medium')
    for i, d in enumerate(rows):
        r = d['result']
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"<div class='pg-row'><b style='font-size:16px'>{esc(r['supplier'])}</b>{pill(d['status'])}</div>"
                            f"<div class='pg-sub'>{esc(pack_label(d['file_name']))}{' · Item ' + esc(r['item_code']) if r['item_code'] else ''} · decided by {esc(d['status_source'])}</div>", unsafe_allow_html=True)
                if status == 'Approved':
                    st.markdown(f"{esc(r['description'])}<br><b>Unit Price: {esc(money(r['unit_price']) if r['unit_price'] is not None else None)}</b>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**Reason for Rejection**<div class='pg-sub' style='color:#ffb4b4'>{esc(basis_text(d))}</div>", unsafe_allow_html=True)
                    for f in [x for x in r['findings'] if x['severity'] == 'REJECT']:
                        st.markdown(f"<div class='pg-sub'>Rule {esc(f['rule'])} · Evidence from PDF</div><div class='pg-evidence'>“{esc(f['evidence'])}”</div>", unsafe_allow_html=True)
                    for line in limit_details(r, request):
                        st.caption(line)
                st.button('View Full Validation Details →' if status == 'Rejected' else 'View Details →', key=f'open_{status}_{d["id"]}', on_click=go, args=(status, d['id']), use_container_width=True)

def page_review():
    if apply_open_doc(): return
    pending = [d for d in docs if d['status'] == 'Human Review']
    st.title('Human Review Queue')
    st.caption(f'{len(pending)} Pending')
    st.info('The AI recommendation and the human decision are stored separately. Reviewer name, time, comment and final decision are saved to the audit log.')
    if not pending:
        st.success('Nothing waiting for review.')
    for d in pending:
        r = d['result']
        info = d['status_source'] == 'Info requested'
        with st.container(border=True):
            st.markdown(f"<div class='pg-row'><b style='font-size:17px'>{esc(r['supplier'])}</b><span class='pg-pill pg-warn'>{'Awaiting information' if info else 'Pending Review'}</span></div><div class='pg-sub'>{esc(pack_label(d['file_name']))} · Quotation {esc(r['quotation_no'])}</div>", unsafe_allow_html=True)
            if info:
                last = d['reviews'][-1]
                st.caption(f"More information requested by {last['reviewer']} on {last['created_at']}: {last['comment']}")
            for f in r['findings']:
                st.markdown(f"**Issue [{esc(f['rule'])}]:** {esc(f['message'])}<div class='pg-evidence'>“{esc(f['evidence'])}”</div>", unsafe_allow_html=True)
            st.markdown("**AI Recommendation:** Needs a person to check")
            for line in limit_details(r, request):
                st.caption(line)
            review_form(d, 'queue')
            st.button('Open full details & PDF →', key=f'hr_open_{d["id"]}', on_click=go, args=('Human Review', d['id']))

def page_pr():
    st.title('Purchase Request')
    st.caption('PR-2026-114 — limits used by every validation rule.')
    quotes: dict[str, list] = {}
    for d in docs:
        quotes.setdefault(d['result']['item_code'], []).append(d)
    rows = []
    for code, rq in request.items():
        q = quotes.get(code, [])
        prices = [x['result']['unit_price'] for x in q if x['result']['unit_price'] is not None]
        rows.append({'Item': code, 'Description': rq['Description'], 'Unit': rq['Unit'], 'Quantity requested': rq['quantity'], 'Maximum unit price (BDT)': rq['max_price'],
                     'Quotes received': len(q), 'Approved quotes': sum(x['status'] == 'Approved' for x in q), 'Lowest quoted price (BDT)': min(prices) if prices else None})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with st.expander('Company rules applied'):
        rules = DATA / 'company-rules.md'
        st.markdown(rules.read_text(encoding='utf-8') if rules.exists() else 'company-rules.md not found.')

def page_reports():
    st.title('Reports & Analytics')
    if not docs:
        st.info('No data yet.'); return
    changed = sum(1 for d in docs if d['status_source'] in ('Admin override', 'Human review') and d['status'] != {'Approve': 'Approved', 'Reject': 'Rejected', 'Needs a person to check': 'Human Review'}[d['ai_decision']])
    m = st.columns(5)
    m[0].metric('Documents', len(docs)); m[1].metric('Approved', counts['Approved']); m[2].metric('Rejected', counts['Rejected'])
    m[3].metric('Human Review', counts['Human Review']); m[4].metric('Final ≠ AI decision', changed)
    left, right = st.columns(2, gap='medium')
    with left:
        st.subheader('Documents by final status')
        st.bar_chart(pd.DataFrame({'Documents': [counts['Approved'], counts['Rejected'], counts['Human Review']]}, index=['Approved', 'Rejected', 'Human Review']))
    with right:
        st.subheader('Most frequent rule findings')
        tally: dict[tuple, int] = {}
        for d in docs:
            for f in d['result']['findings']:
                tally[(f['rule'], f['severity'])] = tally.get((f['rule'], f['severity']), 0) + 1
        st.dataframe(pd.DataFrame([{'Rule ID': k[0], 'Severity': k[1], 'Count': v} for k, v in sorted(tally.items(), key=lambda x: -x[1])]), hide_index=True, use_container_width=True)
    export = pd.DataFrame([{
        'document_id': d['id'], 'file': d['file_name'], 'supplier': d['result']['supplier'], 'quotation_no': d['result']['quotation_no'], 'item': d['result']['item_code'],
        'quantity': d['result']['quantity'], 'unit_price_bdt': d['result']['unit_price'], 'ai_decision': d['ai_decision'],
        'human_review': d['reviews'][-1]['decision'] if d['reviews'] else '', 'reviewer': d['reviews'][-1]['reviewer'] if d['reviews'] else '',
        'reviewer_comment': d['reviews'][-1]['comment'] if d['reviews'] else '', 'admin_override': d['overrides'][-1]['decision'] if d['overrides'] else '',
        'override_reason': d['overrides'][-1]['reason'] if d['overrides'] else '', 'final_status': d['status'], 'decided_by': d['status_source'],
        'rule_ids': '; '.join(f['rule'] for f in d['result']['findings']), 'reasons': ' | '.join(f['message'] for f in d['result']['findings']),
        'evidence': ' | '.join(f['evidence'] for f in d['result']['findings'])} for d in docs])
    audit = pd.DataFrame(store.audit_log())
    st.subheader('Export')
    a, b = st.columns(2)
    a.download_button('⇩ Documents report (CSV)', export.to_csv(index=False).encode('utf-8-sig'), 'procureguard-documents.csv', 'text/csv', use_container_width=True)
    b.download_button('⇩ Audit log (CSV)', audit.to_csv(index=False).encode('utf-8-sig'), 'procureguard-audit-log.csv', 'text/csv', use_container_width=True)
    with st.expander('Audit log'):
        st.dataframe(audit, hide_index=True, use_container_width=True)

# ---------- sidebar & routing ----------
with st.sidebar:
    st.markdown("<div style='padding:10px 4px 14px'><div style='font-size:26px;color:#25d5bc'>⬡</div><div style='font-family:Space Grotesk;font-size:20px;font-weight:700'>ProcureGuard <span style='color:#23cdb4'>AI</span></div><div style='font-size:11px;color:#8ca7a0'>DOCUMENT INTELLIGENCE</div></div>", unsafe_allow_html=True)
    def nav_label(p: str) -> str:
        extra = {'Approved': counts['Approved'], 'Rejected': counts['Rejected'], 'Human Review': counts['Human Review'], 'All Documents': len(docs)}.get(p)
        return f"{ICONS[p]}  {p}" + (f'  ({extra})' if extra is not None else '')
    st.radio('Navigation', PAGES, key='nav', format_func=nav_label, label_visibility='collapsed', on_change=clear_selection)
    st.divider()
    st.text_input('Signed in as', key='user_name', placeholder='Your name (saved in audit log)')
    st.selectbox('Role', ['Reviewer', 'Admin'], key='role')
    st.divider()
    st.caption('● Local processing · no external AI API')

if 'flash' in ss:
    kind, text = ss.pop('flash')
    getattr(st, kind)(text)

page = ss.nav
{'Dashboard Overview': page_dashboard, 'Upload Documents': page_upload, 'All Documents': page_all,
 'Approved': lambda: page_status('Approved'), 'Rejected': lambda: page_status('Rejected'),
 'Human Review': page_review, 'Purchase Request': page_pr, 'Reports & Analytics': page_reports}[page]()

st.divider()
st.caption('ProcureGuard AI is a decision-support prototype. Ambiguous, missing, scanned or out-of-template documents go to a person. No supplier is automatically paid or contracted.')
