"""Regression Test: Credential & TOTP Secret Redaction Guard.

Enforces that test harnesses, runners, scripts, and generated markdown artifacts
never leak plaintext credentials, passwords, session cookies, or TOTP secrets.
"""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Known leaked patterns from previous runs that must NEVER reappear
KNOWN_LEAKED_DIGESTS = ['7f265682edae64944d0cd588f3e86b93cfe239fc23f1d038e6082f876dbc4adf', '316788499ba84fbe82ca2d04551db8bc3549c8d72cc6a3937654e4cf4bb7b4e5', 'c0ba87efbba2a8648259f2479e777011bea97ebe56215cd56863a1fd0665cbf9', 'c8a0b4fe9fc38b0f1f6a6080808c55370111b081b043f82c8fc33d5a688dbc0f', 'f4d013f2c1854c44339301ea2af0be79a52e7ce4d6f811e383bb22f4ce5f3c6b', '6a6cbbd7055b5ffaf65a421b580d518572adc7b1704ba26f254d389487ba5fd5', '141c1a2445ad115613021b5f56e07654d5cef902ff911d40c9cdf0950efadf25', '71da476adbba493bd2481da0e4a064567066c438b08974bd1ebc360aa328cf64']

# Regex for base32 RFC 4648 32-char TOTP secret strings
# Disallow raw base32 secrets in documentation/reports
TOTP_B32_EXPLICIT_REGEX = re.compile(r"Secret\s+[`'\"]([A-Z2-7]{26,32})[`'\"]", re.IGNORECASE)


class TestSecretRedactionGuard(unittest.TestCase):
    def test_no_leaked_credentials_in_reports(self):
        """Scans all markdown documents and audit reports for leaked credentials."""
        docs_dir = ROOT / "docs"
        violating_files = []

        for md_file in docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern in re.findall(r'[A-Za-z0-9_!~-]{8,}', content):
                if hashlib.sha256(pattern.encode()).hexdigest() not in KNOWN_LEAKED_DIGESTS:
                    continue
                if pattern in content:
                    violating_files.append((str(md_file.relative_to(ROOT)), f"Matched historical credential digest"))

            # Check explicit TOTP secret declaration
            match = TOTP_B32_EXPLICIT_REGEX.search(content)
            if match:
                val = match.group(1)
                if "REDACTED" not in val:
                    violating_files.append((str(md_file.relative_to(ROOT)), f"Explicit unredacted TOTP secret format"))

        self.assertEqual(
            violating_files,
            [],
            f"Security Violation: Found unredacted credentials/TOTP secrets in artifacts: {violating_files}",
        )

    def test_no_hardcoded_secrets_in_new_audit_scripts(self):
        """Ensures scripts do not hardcode plaintext staging TOTP secrets."""
        scripts_dir = ROOT / "scripts"
        violating_scripts = []

        for script in scripts_dir.glob("*.py"):
            try:
                content = script.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern in re.findall(r'[A-Za-z0-9_!~-]{8,}', content):
                if hashlib.sha256(pattern.encode()).hexdigest() not in KNOWN_LEAKED_DIGESTS[:6]:
                    continue
                if pattern in content:
                    violating_scripts.append((str(script.relative_to(ROOT)), f"Hardcoded historical TOTP credential"))

        self.assertEqual(
            violating_scripts,
            [],
            f"Security Violation: Scripts contain hardcoded TOTP secrets: {violating_scripts}",
        )


if __name__ == "__main__":
    unittest.main()
