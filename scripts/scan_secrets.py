"""Repository Secret Scanner for BASE-03.
Scans git tracked and untracked files for exposed API keys, private keys, and passwords.
Uses porcelain output to discover all tracked and untracked files.
Excludes virtual environments, git metadata, and local app data.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Sensitive patterns
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"\bAIzaSy[0-9A-Za-z_-]{33}\b"), "Google API Key (Production)"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS Access Key"),
    (re.compile(r"(?i)(?:api_key|secret_key|password)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]"), "Hardcoded High-Entropy Secret"),
]

IGNORED_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", "tmp", "coverage"
}

IGNORED_EXTS = {
    ".png", ".jpg", ".jpeg", ".docx", ".pdf", ".sqlite", ".zip", ".tar", ".gz"
}

def is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIRS:
            return True
    if path.suffix.lower() in IGNORED_EXTS:
        return True
    return False

def scan_files():
    # Discover all files via git status porcelain
    res = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=str(ROOT),
        capture_output=True,
        text=True
    )
    
    # Also get tracked files
    res_tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=str(ROOT),
        capture_output=True,
        text=True
    )

    all_files = set()
    for line in res_tracked.stdout.splitlines():
        if line.strip():
            all_files.add(ROOT / line.strip())

    for line in res.stdout.splitlines():
        line = line.strip()
        if len(line) > 3:
            path_str = line[3:].strip().strip('"')
            all_files.add(ROOT / path_str)

    print(f"Total candidate files to scan: {len(all_files)}")

    findings = []
    scanned_count = 0

    for fpath in all_files:
        if not fpath.is_file() or is_ignored(fpath):
            continue
        
        # Don't scan this scanner itself or known test file with redaction test fixtures
        if fpath.name in ("scan_secrets.py", "security_audit.py", "test_prompt_injection_and_secret_exfil.py"):
            continue

        scanned_count += 1
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern, label in SECRET_PATTERNS:
            matches = pattern.findall(content)
            for m in matches:
                # Ignore dummy/placeholder secrets in documentation and test fixtures
                if any(dummy in str(m) for dummy in ["EXAMPLE", "TEST", "Aa1!", "dummy", "placeholder", "xxx"]):
                    continue
                # Ignore reference hashes
                if len(str(m)) == 64 and all(c in "0123456789abcdefABCDEF" for c in str(m)):
                    continue
                findings.append((str(fpath.relative_to(ROOT)), label))

    print(f"Scanned text files: {scanned_count}")
    if findings:
        print(f"FAIL: Found {len(findings)} potential secret exposures:")
        for file_rel, label in findings[:10]:
            print(f"  - {file_rel}: {label}")
        sys.exit(1)
    else:
        print("SUCCESS: 0 real secrets or private credentials found in repository files.")
        sys.exit(0)

if __name__ == "__main__":
    scan_files()
