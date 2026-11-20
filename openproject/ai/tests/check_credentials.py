import json
import os
from pathlib import Path
import subprocess

rt = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
accounts_stage = json.loads((rt / "stage/accounts.json").read_text(encoding="utf-8"))

accounts_op = {}
op_acc_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject/accounts.json"
if op_acc_path.is_file():
    accounts_op = json.loads(op_acc_path.read_text(encoding="utf-8"))

ruby_code = """
require "json"
results = {}

candidates = [
  ["stage-owner", "PUBLICATION_REDACTED"],
  ["ba-pm", "PUBLICATION_REDACTED"],
  ["pm", "PUBLICATION_REDACTED"],
  ["be", "PUBLICATION_REDACTED"],
  ["fe", "PUBLICATION_REDACTED"],
  ["qa", "PUBLICATION_REDACTED"],
  ["op-owner", "PUBLICATION_REDACTED"],
  ["ba-pm", "PUBLICATION_REDACTED"],
  ["pm", "PUBLICATION_REDACTED"],
  ["be", "PUBLICATION_REDACTED"],
  ["fe", "PUBLICATION_REDACTED"],
  ["qa", "PUBLICATION_REDACTED"]
]

candidates.each do |login, pwd|
  u = User.find_by(login: login)
  if u
    valid = u.check_password?(pwd) rescue false
    results["#{login}::#{pwd[0..8]}..."] = { id: u.id, valid: valid }
  end
end

puts "CHECK_RESULTS=" + JSON.generate(results)
"""

r = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code,
    text=True,
    capture_output=True,
    timeout=60
)
for line in r.stdout.splitlines():
    if line.startswith("CHECK_RESULTS="):
        res = json.loads(line.split("=", 1)[1])
        for k, v in res.items():
            print(f"  {k} -> ID: {v['id']}, Valid: {v['valid']}")
if r.stderr:
    print("STDERR:", r.stderr)
