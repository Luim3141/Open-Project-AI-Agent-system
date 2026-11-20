"""Pinned text-layer PDFs only. Runs as a short-lived child of local_loaders."""
import logging
from pathlib import Path
import sys


def extract(path):
    if sys.platform!='win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(192*1024*1024,192*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(10,10))
    from pypdf import PdfReader
    logging.disable(logging.CRITICAL)
    raw=Path(path).read_bytes()
    if len(raw)>262144 or not raw.startswith(b'%PDF-'):
        raise ValueError('PDF_FILE_INVALID_OR_TOO_LARGE')
    from io import BytesIO
    reader=PdfReader(BytesIO(raw),strict=True)
    if reader.is_encrypted:raise ValueError('PDF_ENCRYPTED_NOT_SUPPORTED')
    if not 1<=len(reader.pages)<=64:raise ValueError('PDF_PAGE_LIMIT')
    # shortcut: text-layer PDFs only, add a separately bounded OCR pipeline when scanned sources are required.
    output=[];size=0;streams=0
    for page in reader.pages:
        content=page.get_contents()
        decoded=len(content.get_data()) if content else 0
        streams+=decoded
        if decoded>1048576 or streams>4194304:raise ValueError('PDF_STREAM_SIZE_LIMIT')
        text=page.extract_text()
        if not text or not text.strip():raise ValueError('PDF_PAGE_WITHOUT_TEXT_OCR_REQUIRED')
        size+=len(text.encode('utf-8'))+2
        if size>262144:raise ValueError('PDF_TEXT_SIZE_LIMIT')
        output.append(text)
    return '\n\n'.join(output)


if __name__=='__main__':
    try:
        sys.stdout.buffer.write(extract(sys.argv[1]).encode('utf-8'))
    except Exception as error:
        code=str(error)
        sys.stderr.write(code if code.startswith('PDF_') and code.replace('_','').isupper() else 'PDF_PARSE_FAILED')
        sys.exit(1)
