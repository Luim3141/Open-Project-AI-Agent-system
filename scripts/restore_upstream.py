"""Reconstruct pinned vendor trees and the separate development variant."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT):
    subprocess.run(args, cwd=cwd, check=True)


def clone_pinned(repository, commit, destination):
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    run('git', 'init', str(destination))
    run('git', 'remote', 'add', 'origin', repository, cwd=destination)
    run('git', 'fetch', '--depth=1', 'origin', commit, cwd=destination)
    run('git', 'checkout', '--detach', 'FETCH_HEAD', cwd=destination)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=destination, text=True).strip()
    if actual != commit:
        raise RuntimeError('Upstream commit does not match lock')


def main():
    lock = json.loads((ROOT/'openproject/upstream-lock.json').read_text())
    targets = [(ROOT/'openproject/upstream'/name, lock[name]) for name in ('openproject', 'compose')]
    development = ROOT/'openproject/development/core'
    # Preflight every path before creating any checkout; partial failures stay for inspection.
    for path in [p for p, _ in targets] + [development]:
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite {path}; inspect existing source first')
    for path, record in targets:
        clone_pinned(record['repository'], record['commit'], path)
    clone_pinned(lock['openproject']['repository'], lock['openproject']['commit'], development)
    patch = ROOT/'openproject/development-patch/core.patch'
    run('git', 'apply', '--check', str(patch), cwd=development)
    run('git', 'apply', str(patch), cwd=development)
    extra = ROOT/'openproject/development-patch/untracked'
    for source in extra.rglob('*'):
        if source.is_file():
            dest = development/source.relative_to(extra)
            if dest.exists():
                raise FileExistsError(f'Untracked source would overwrite {dest}')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    print('Pinned upstream and separate development source restored; runtime unchanged.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
