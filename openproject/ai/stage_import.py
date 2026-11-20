import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_wbs

parser = argparse.ArgumentParser()
parser.add_argument("--runtime", required=True)
args = parser.parse_args()
runtime = Path(args.runtime)
config = json.loads((runtime / "bootstrap.json").read_text())
accounts = json.loads((runtime / "accounts.json").read_text())
by_role = {a["role"]: config["users"][a["email"].lower()] for a in accounts["users"]}
for row in csv.DictReader((runtime / "wbs-snapshot.csv").open(encoding="utf-8-sig", newline="")):
    role = row["Proposed Role"]
    if role not in by_role:
        role = {"BA": "BA-PM", "Tester": "QA", "Dev BE": "BE", "Dev FE": "FE"}.get(role, role)
    config["users"][row["Proposed Assignee Email"].lower()] = by_role[role]
(runtime / "bootstrap.json").write_text(json.dumps(config), encoding="utf-8")
import_wbs.BASE = "http://127.0.0.1:18091"
import_wbs.import_snapshot(runtime)
