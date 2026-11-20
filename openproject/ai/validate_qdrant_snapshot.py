"""Read-only collection snapshot check; a matching download checksum is insufficient."""
import json
import re
import tarfile
from pathlib import PurePosixPath


def validate_snapshot(path):
    checked, invalid, names = [], [], set()
    with tarfile.open(path, 'r:') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or member.name in names or len(names) >= 10000:
                raise ValueError('UNTRUSTED_SNAPSHOT_PATH_OR_SIZE')
            names.add(member.name)
            if not re.fullmatch(r'\d+/wal/first-index', member.name):
                continue
            checked.append(member.name)
            try:
                if not member.isfile() or not 0 < member.size <= 4096:
                    raise ValueError()
                value = json.loads(archive.extractfile(member).read())
                if set(value) != {'ack_index'} or type(value['ack_index']) is not int or value['ack_index'] < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                invalid.append(member.name)
    return {'status': 'INVALID_WAL_METADATA' if invalid else 'WAL_METADATA_VALID' if checked else 'WAL_METADATA_NOT_FOUND',
        'checked_entries': checked, 'invalid_entries': invalid,
        'limitation': 'Valid metadata does not prove recovery; isolated restore and point comparison are still required'}


if __name__ == '__main__':
    import sys
    result = validate_snapshot(sys.argv[1])
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'WAL_METADATA_VALID' else 2)
