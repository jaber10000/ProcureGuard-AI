"""Command-line runner for ProcureGuard's fixed-step pipeline."""
from pathlib import Path
import csv
from src.pipeline import run_folder

ROOT=Path(__file__).parent
results=run_folder(ROOT/'data')
print(f"Checked {len(results)} supplier documents")
for result in results:
    print(f"{result.file_name:22} | {result.decision:26} | {result.supplier}")
    for finding in result.findings:
        print(f"  - [{finding.rule}] {finding.message}")
output=ROOT/'procureguard-results.csv'
with output.open('w', newline='', encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f, fieldnames=['file','supplier','decision','rule_ids','reasons'])
    writer.writeheader()
    for result in results:
        writer.writerow({'file':result.file_name,'supplier':result.supplier,'decision':result.decision,
                         'rule_ids':'; '.join(x.rule for x in result.findings),
                         'reasons':' | '.join(x.message for x in result.findings)})
print(f"\nCSV report written to {output.name}")
