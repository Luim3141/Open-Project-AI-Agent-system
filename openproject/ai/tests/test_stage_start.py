import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "Windows PowerShell startup seam")
class StageStartTests(unittest.TestCase):
    def test_resume_keeps_pinned_containers_and_refuses_changed_image(self):
        script = Path(__file__).resolve().parents[1] / "Manage-OpenProjectAI.ps1"
        with tempfile.TemporaryDirectory() as folder:
            runtime = Path(folder) / "QLDAPM/openproject-ai"
            runtime.mkdir(parents=True)
            (runtime / ".env").write_text("# synthetic startup fixture, no credentials\n")
            (runtime / "stage-image-lock.json").write_text(json.dumps(
                {service: "sha256:" + "a" * 64 for service in ("db", "staging-web", "staging-gateway")}))
            # External Docker boundary only; no engine, live state, credential or Windows setting is touched.
            stub = """
function docker {
  $global:LASTEXITCODE=0
  if ($args[0] -eq 'info') { return 'fixture-engine' }
  if ($args[0] -eq 'inspect') {
    $image='sha256:' + ('a' * 64)
    if ($env:STAGE_CHANGED -eq 'true') { $image='sha256:' + ('b' * 64) }
    return (@{Image=$image;Config=@{Labels=@{'com.docker.compose.project'='qldapm-ai-stage'}}} | ConvertTo-Json -Depth 4 -Compress)
  }
  if ($args[0] -eq 'start' -and $env:STAGE_CHANGED -ne 'true') { return 'fixture-started' }
  throw 'Unexpected mutation instead of refusal'
}
& $env:STAGE_SCRIPT -Action StartStage
"""
            for changed in (False, True):
                with self.subTest(changed=changed):
                    result = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-Command", stub],
                        env={**os.environ, "LOCALAPPDATA": folder, "STAGE_SCRIPT": str(script),
                             "STAGE_CHANGED": str(changed).lower()}, capture_output=True, text=True, timeout=15)
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode == 0, not changed, output)
                    self.assertIn("image/ownership mismatch" if changed else "Existing key/provider state retained", output)
