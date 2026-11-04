from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pipeline import run_folder

DATA=Path(__file__).resolve().parents[1]/'data'
EXPECTED={
 'supplier-pack-01.pdf':'Approve', 'supplier-pack-02.pdf':'Approve',
 'supplier-pack-03.pdf':'Reject', 'supplier-pack-04.pdf':'Needs a person to check',
 'supplier-pack-05.pdf':'Reject', 'supplier-pack-06.pdf':'Reject',
 'supplier-pack-07.pdf':'Needs a person to check', 'supplier-pack-08.pdf':'Reject',
 'supplier-pack-09.pdf':'Needs a person to check', 'supplier-pack-10.pdf':'Reject',
}
def test_all_sample_decisions():
    results=run_folder(DATA)
    actual={r.file_name:r.decision for r in results}
    assert actual==EXPECTED

def test_rejects_have_evidence_or_explicit_absence():
    for r in run_folder(DATA):
        if r.decision=='Reject':
            assert any(f.severity=='REJECT' for f in r.findings)
            assert all(f.evidence for f in r.findings if f.severity=='REJECT')
