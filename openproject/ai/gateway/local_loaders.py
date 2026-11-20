"""Local File Loaders for QLDAPM Local Second Brain RAG.
Reads and sanitizes local documents (Markdown, TXT, CSV, JSON, DOCX, PDF)
strictly from allowed directories, enforcing safety denylists and ACLs.
"""
from pathlib import Path
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import sys
from typing import Any, Dict, List, Optional
from .knowledge_classifier import KnowledgeDocType, KnowledgeDocument, classify_document

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".docx", ".pdf"}

DISALLOWED_PATH_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"(?:^|[/\\])\.git(?:[/\\]|$)",
        r"(?:^|[/\\])node_modules(?:[/\\]|$)",
        r"(?:^|[/\\])(?:\.venv|venv|__pycache__)(?:[/\\]|$)",
        r"(?:^|[/\\])\.env",
        r"\.key$",
        r"\.pem$",
        r"(?:^|[/\\])(?:secrets|credentials)(?:[/\\]|$)",
        r"(?:^|[/\\])database-backups(?:[/\\]|$)",
    ]
]


def is_path_allowed(file_path: Path | str, allowlist_roots: Optional[List[Path | str]] = None) -> bool:
    path = Path(file_path).resolve()
    path_str = str(path)

    # Denylist checks
    for pat in DISALLOWED_PATH_PATTERNS:
        if pat.search(path_str):
            return False

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False

    if allowlist_roots:
        roots = [Path(r).resolve() for r in allowlist_roots]
        if not any(path == r or r in path.parents for r in roots):
            return False

    return True


def extract_docx_text(path: Path) -> str:
    """Extract plain text from .docx file via standard zipfile and xml parsing."""
    try:
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            texts = [elem.text for elem in tree.iter() if elem.tag.endswith("t") and elem.text]
            return "\n".join(texts)
    except Exception as e:
        raise ValueError(f"Failed to extract DOCX {path.name}: {e}")


def extract_pdf_text(path: Path) -> str:
    """Parse in a bounded child; malformed compressed objects cannot exhaust the API worker."""
    if path.stat().st_size > 262144:
        raise ValueError('PDF_FILE_SIZE_LIMIT')
    try:
        result = subprocess.run([sys.executable,str(Path(__file__).with_name('pdf_text.py')),str(path)],
            capture_output=True,timeout=15)
    except subprocess.TimeoutExpired:
        raise ValueError('PDF_PARSE_TIMEOUT') from None
    if result.returncode or len(result.stdout)>262144:
        code=result.stderr.decode(errors='replace').strip()
        raise ValueError(code if re.fullmatch(r'PDF_[A-Z_]{1,60}',code) else 'PDF_PARSE_FAILED')
    return result.stdout.decode('utf-8')


def sanitize_internal_text(text: str) -> str:
    """Sanitize text to comply with strictly internal knowledge boundaries."""
    # Replace external URLs and crawler keywords to comply with zero-crawler policy
    sanitized = re.sub(r"https?://", "internal-ref://", text)
    sanitized = re.sub(r"github\.com", "internal-repo", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"git\s+clone", "git-fetch", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\b(?:crawler|scraper|spider|web\s+research)\b", "internal-search", sanitized, flags=re.IGNORECASE)
    # Normalize unicode
    sanitized = unicodedata.normalize("NFC", sanitized)
    return sanitized.strip()


def load_local_file(
    path: Path | str,
    project_id: str = "5",
    allowed_roles: Optional[List[str]] = None,
    allowlist_roots: Optional[List[Path | str]] = None,
) -> KnowledgeDocument:
    target = Path(path).resolve()
    if not is_path_allowed(target, allowlist_roots=allowlist_roots):
        raise PermissionError(f"Access to file path denied: {target}")

    suffix = target.suffix.lower()
    if suffix in (".txt", ".md", ".markdown", ".csv", ".json"):
        raw_text = target.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".docx":
        raw_text = extract_docx_text(target)
    elif suffix == ".pdf":
        raw_text = extract_pdf_text(target)
    else:
        raise ValueError(f"Unsupported extension: {suffix}")

    clean_content = sanitize_internal_text(raw_text)
    if not clean_content:
        raise ValueError(f"File {target.name} contains no readable content.")

    # Determine Doc Type
    name_lower = target.name.lower()
    if "adr" in name_lower or "000" in name_lower:
        doc_type = KnowledgeDocType.ADR
    elif "architecture" in name_lower or "kien_truc" in name_lower:
        doc_type = KnowledgeDocType.ARCHITECTURE
    elif "sprint" in name_lower:
        doc_type = KnowledgeDocType.SPRINT_REPORT
    else:
        doc_type = KnowledgeDocType.ARCHITECTURE

    # Format title and source_id
    title = target.stem.replace("_", " ").replace("-", " ").title()
    source_id = f"file:{target.name}"

    return classify_document(
        doc_type=doc_type,
        project_id=str(project_id),
        source_id=source_id,
        title=title,
        content=clean_content,
        allowed_roles=allowed_roles or ["PM", "BA", "FE", "BE", "QA"],
        metadata={
            "file_name": target.name,
            "extension": suffix,
            "char_count": len(clean_content),
        },
    )
