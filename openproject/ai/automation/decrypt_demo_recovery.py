"""Portable bootstrap: authenticate/decrypt into a NEW folder; never start or restore services."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAGIC = b'QLDAPM-DEMO-RECOVERY-V1\n'


def unpack(ciphertext, key_file, output):
    ciphertext, key_file, output = map(Path, (ciphertext, key_file, output))
    if output.exists(): raise ValueError('NEW_EMPTY_DESTINATION_REQUIRED')
    if ciphertext.resolve() == key_file.resolve(): raise ValueError('SEPARATE_KEY_FILE_REQUIRED')
    key = key_file.read_bytes()
    if len(key) != 32: raise ValueError('RECOVERY_KEY_LENGTH_INVALID')
    output.mkdir(parents=True, mode=0o700)
    temporary = output / 'authenticated-payload.tar'
    try:
        with ciphertext.open('rb') as incoming:
            if incoming.read(len(MAGIC)) != MAGIC: raise ValueError('RECOVERY_FORMAT_INVALID')
            nonce = incoming.read(12); incoming.seek(-16, 2); tag = incoming.read(16)
            remaining = incoming.tell() - len(MAGIC) - 28
            if remaining <= 0: raise ValueError('RECOVERY_TRUNCATED')
            incoming.seek(len(MAGIC) + 12)
            reader = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor(); reader.authenticate_additional_data(MAGIC)
            with temporary.open('xb') as destination:
                while remaining:
                    block = incoming.read(min(1024 * 1024, remaining))
                    if not block: raise ValueError('RECOVERY_TRUNCATED')
                    destination.write(reader.update(block)); remaining -= len(block)
                destination.write(reader.finalize())
        with tarfile.open(temporary, 'r:') as archive:
            names = set()
            for item in archive:
                name = PurePosixPath(item.name)
                if name.is_absolute() or '..' in name.parts or ':' in item.name or '\\' in item.name or item.name in names or not (item.isfile() or item.isdir()):
                    raise ValueError('UNSAFE_RECOVERY_ARCHIVE')
                names.add(item.name)
            if 'manifest.json' not in names: raise ValueError('RECOVERY_MANIFEST_REQUIRED')
            archive.extractall(output, filter='data')
        manifest = json.loads((output / 'manifest.json').read_text(encoding='utf8'))
        for relative, expected in manifest['files'].items():
            path = output / relative
            if not path.resolve().is_relative_to(output.resolve()) or not path.is_file(): raise ValueError('INVALID_MANIFEST_PATH')
            with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if path.stat().st_size != expected['bytes'] or digest != expected['sha256']: raise ValueError('RESTORE_CHECKSUM_FAILED')
        return {'status': 'DECRYPTED_CHECKSUM_VERIFIED_NO_SERVICES_STARTED', 'files': len(manifest['files']),
                'label': manifest['label'], 'created_utc': manifest['created_utc'], 'destination': str(output)}
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ciphertext', required=True, type=Path); parser.add_argument('--key-file', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(unpack(args.ciphertext, args.key_file, args.output), indent=2))
