"""Read-only, key-free verification of this exact old-key recovery kit's copied ciphertext directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat


# Pins come from Phase2 creation evidence plus read-only FORMAT.json inventory; never from the copy.
EXPECTED = {
    'n8n-recovery-v1.aesgcm': '47cab825e5e23a130bcbba298c0b1cbe344375d21c28753a74a3797fddcd4155',
    'portable_recovery_restore.js': 'f5cd2e4e6996796a61fe60d65038e005a248359143fc7dab17f52310d328e388',
    'FORMAT.json': 'b23a0e93dce3847cd7ec56e44b8c7a120c6594a5a62266ce058d4e5f1456b45a',
}
MAX_FILE_BYTES = 32 * 1024 * 1024


def reject_link(path):
    info = path.lstat()
    if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
        raise ValueError('CIPHERTEXT_LINK_DENIED')
    return info


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(directory):
    directory = Path(directory).absolute()
    for path in (directory, *directory.parents):
        reject_link(path)
    if not directory.is_dir() or {path.name for path in directory.iterdir()} != set(EXPECTED):
        raise ValueError('CIPHERTEXT_FILE_SET_DENIED')
    for name in EXPECTED:
        info = reject_link(directory / name)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('CIPHERTEXT_REGULAR_FILE_REQUIRED')
        if not 0 < info.st_size <= MAX_FILE_BYTES:
            raise ValueError('CIPHERTEXT_SIZE_DENIED')
    for name, expected in EXPECTED.items():
        if file_hash(directory / name) != expected:
            raise ValueError('CIPHERTEXT_HASH_MISMATCH')
    return {'status': 'CIPHERTEXT_COPY_BYTES_VERIFIED', 'utc': datetime.now(timezone.utc).isoformat(),
            'files_sha256': dict(EXPECTED), 'key_read': False, 'decrypt_or_execution': False,
            'offhost_custody': 'OWNER_ATTESTATION_PENDING', 'destination_acl': 'OWNER_CHECK_REQUIRED',
            'physical_restore': 'NOT_TESTED', 'snapshot': '2026-11-01 old-key cold snapshot; MAIN unchanged'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ciphertext-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.ciphertext_dir), indent=2))
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'FAILED', 'error_type': type(error).__name__, 'key_read': False}))
        raise SystemExit(1)
