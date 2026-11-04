"""Persistent store for ProcureGuard AI.

Design rules (from the product spec):
* The AI decision is stored once and never modified.
* Human-review decisions and admin overrides live in their own tables.
* Every state change is written to an append-only audit log.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

AI_TO_STATUS = {'Approve': 'Approved', 'Reject': 'Rejected', 'Needs a person to check': 'Human Review'}
REVIEW_TO_STATUS = {'Approve': 'Approved', 'Reject': 'Rejected', 'Request More Information': 'Human Review'}

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents(
  id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
  uploaded_at TEXT NOT NULL, source TEXT NOT NULL, ai_decision TEXT NOT NULL, supplier TEXT, result_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reviews(
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL, reviewer TEXT NOT NULL,
  decision TEXT NOT NULL, comment TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS overrides(
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL, admin TEXT NOT NULL,
  decision TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, actor TEXT NOT NULL,
  action TEXT NOT NULL, doc_id INTEGER, details TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""

def now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Store:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.pdf_dir = self.root / 'pdfs'
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / 'procureguard.db'
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ---------- files ----------
    def pdf_path(self, digest: str) -> Path:
        return self.pdf_dir / f'{digest}.pdf'

    def find_by_hash(self, digest: str):
        with self._conn() as c:
            return c.execute('SELECT id, file_name FROM documents WHERE sha256=?', (digest,)).fetchone()

    # ---------- documents ----------
    def add_document(self, file_name: str, digest: str, result: dict, source: str, actor: str = 'system') -> int:
        with self._conn() as c:
            cur = c.execute(
                'INSERT INTO documents(file_name, sha256, uploaded_at, source, ai_decision, supplier, result_json) VALUES(?,?,?,?,?,?,?)',
                (file_name, digest, now(), source, result['decision'], result.get('supplier', ''), json.dumps(result, ensure_ascii=False)))
            doc_id = cur.lastrowid
            c.execute('INSERT INTO audit_log(ts, actor, action, doc_id, details) VALUES(?,?,?,?,?)',
                      (now(), actor, 'DOCUMENT_PROCESSED', doc_id, f"{file_name}: AI decision = {result['decision']}"))
        return doc_id

    def count(self) -> int:
        with self._conn() as c:
            return c.execute('SELECT COUNT(*) FROM documents').fetchone()[0]

    def list_documents(self) -> list[dict]:
        with self._conn() as c:
            docs = [dict(r) for r in c.execute('SELECT * FROM documents ORDER BY id DESC')]
            reviews = [dict(r) for r in c.execute('SELECT * FROM reviews ORDER BY id')]
            overrides = [dict(r) for r in c.execute('SELECT * FROM overrides ORDER BY id')]
        by_rev: dict[int, list] = {}
        for r in reviews: by_rev.setdefault(r['doc_id'], []).append(r)
        by_ovr: dict[int, list] = {}
        for o in overrides: by_ovr.setdefault(o['doc_id'], []).append(o)
        for d in docs:
            d['result'] = json.loads(d.pop('result_json'))
            d['reviews'] = by_rev.get(d['id'], [])
            d['overrides'] = by_ovr.get(d['id'], [])
            d['status'], d['status_source'] = effective_status(d)
        return docs

    # ---------- human review (separate from the AI decision) ----------
    def add_review(self, doc_id: int, reviewer: str, decision: str, comment: str):
        if decision not in REVIEW_TO_STATUS:
            raise ValueError('Unknown review decision')
        with self._conn() as c:
            row = c.execute('SELECT ai_decision FROM documents WHERE id=?', (doc_id,)).fetchone()
            if row is None:
                raise ValueError('Document not found')
            if row['ai_decision'] != 'Needs a person to check':
                raise ValueError('Only documents routed to human review can receive a reviewer decision. Use an admin override instead.')
            c.execute('INSERT INTO reviews(doc_id, reviewer, decision, comment, created_at) VALUES(?,?,?,?,?)',
                      (doc_id, reviewer, decision, comment, now()))
            c.execute('INSERT INTO audit_log(ts, actor, action, doc_id, details) VALUES(?,?,?,?,?)',
                      (now(), reviewer, 'HUMAN_REVIEW', doc_id, f'{decision}. Comment: {comment or "-"}'))

    # ---------- admin override (AI decision stays untouched) ----------
    def add_override(self, doc_id: int, admin: str, decision: str, reason: str):
        if decision not in ('Approved', 'Rejected'):
            raise ValueError('Override must be Approved or Rejected')
        if not reason.strip():
            raise ValueError('An override reason is mandatory')
        with self._conn() as c:
            row = c.execute('SELECT ai_decision FROM documents WHERE id=?', (doc_id,)).fetchone()
            if row is None:
                raise ValueError('Document not found')
            c.execute('INSERT INTO overrides(doc_id, admin, decision, reason, created_at) VALUES(?,?,?,?,?)',
                      (doc_id, admin, decision, reason.strip(), now()))
            c.execute('INSERT INTO audit_log(ts, actor, action, doc_id, details) VALUES(?,?,?,?,?)',
                      (now(), admin, 'ADMIN_OVERRIDE', doc_id,
                       f"AI decision '{row['ai_decision']}' kept on record; final status set to {decision}. Reason: {reason.strip()}"))

    # ---------- audit ----------
    def log(self, actor: str, action: str, doc_id: int | None, details: str):
        with self._conn() as c:
            c.execute('INSERT INTO audit_log(ts, actor, action, doc_id, details) VALUES(?,?,?,?,?)',
                      (now(), actor, action, doc_id, details))

    def audit_log(self, doc_id: int | None = None) -> list[dict]:
        with self._conn() as c:
            if doc_id is None:
                rows = c.execute('SELECT * FROM audit_log ORDER BY id DESC').fetchall()
            else:
                rows = c.execute('SELECT * FROM audit_log WHERE doc_id=? ORDER BY id DESC', (doc_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- meta ----------
    def get_meta(self, key: str):
        with self._conn() as c:
            row = c.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return row['value'] if row else None

    def set_meta(self, key: str, value: str):
        with self._conn() as c:
            c.execute('INSERT OR REPLACE INTO meta(key, value) VALUES(?,?)', (key, value))


def effective_status(doc: dict) -> tuple[str, str]:
    """Final status = admin override > latest human review > AI decision."""
    if doc['overrides']:
        return doc['overrides'][-1]['decision'], 'Admin override'
    if doc['reviews']:
        last = doc['reviews'][-1]
        label = 'Info requested' if last['decision'] == 'Request More Information' else 'Human review'
        return REVIEW_TO_STATUS[last['decision']], label
    return AI_TO_STATUS[doc['ai_decision']], 'AI'
