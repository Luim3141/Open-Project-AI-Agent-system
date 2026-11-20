import hashlib
import os
import stat
import threading
from pathlib import Path, PurePosixPath


class Workspace:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.lock = threading.RLock()

    def path(self, actor, relative):
        parts = PurePosixPath(relative).parts
        if (not relative or "\\" in relative or ":" in relative or relative.startswith("/") or
                any(p == ".." or p.rstrip(" .").casefold() == ".git" or p.casefold().startswith(".env") for p in parts)):
            raise ValueError("PATH_DENIED")
        base = self.root / str(int(actor))
        target = base.joinpath(*parts)
        cursor = self.root
        for part in target.relative_to(self.root).parts:
            cursor = cursor / part
            if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
                raise ValueError("LINK_DENIED")
        if not target.resolve().is_relative_to(base.resolve()):
            raise ValueError("PATH_DENIED")
        if target.exists() and target.is_file() and target.stat().st_nlink != 1:
            raise ValueError("HARDLINK_DENIED")
        return target

    def read(self, actor, relative):
        with self.lock:
            path = self.path(actor, relative)
            if not path.is_file() or path.stat().st_size > 262144:
                raise ValueError("NOT_A_SMALL_TEXT_FILE")
            data = path.read_bytes()
            return {"path": relative, "content": data.decode("utf-8"), "sha256": hashlib.sha256(data).hexdigest()}

    def write(self, actor, relative, content, expected_hash):
        data = content.encode("utf-8")
        if len(data) > 262144:
            raise ValueError("FILE_TOO_LARGE")
        with self.lock:
            path = self.path(actor, relative)
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "NEW"
            if actual != expected_hash:
                raise ValueError("STALE_CONTENT")
            path.parent.mkdir(parents=True, exist_ok=True)
            # The workspace is writable only through this module; replace avoids partial writes.
            temporary = path.with_name(path.name + ".qldapm-tmp")
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(data)
                temporary.replace(path)
            finally:
                if temporary.exists():
                    temporary.unlink()
            return self.read(actor, relative)

    def list(self, actor, relative="app"):
        directory = self.path(actor, relative)
        if not directory.is_dir():
            raise ValueError("NOT_A_DIRECTORY")
        return [{"path": f"{relative}/{item.name}", "directory": item.is_dir()}
                for item in sorted(directory.iterdir())[:200]
                if not item.name.startswith(".") and not item.is_symlink()]

    def tree_hash(self, actor):
        base = self.root / str(int(actor))
        manifest = hashlib.sha256()
        with self.lock:
            self.path(actor, ".")
            if not base.is_dir():
                raise ValueError("WORKSPACE_NOT_FOUND")
            count, size = 0, 0
            def visit(directory):
                nonlocal count, size
                with os.scandir(directory) as entries:
                    items = sorted(entries, key=lambda entry: entry.name)
                for item in items:
                    name = item.name
                    if name.rstrip(" .").casefold() == ".git" or name.casefold().startswith(".env"):
                        raise ValueError("PATH_DENIED")
                    metadata = item.stat(follow_symlinks=False)
                    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        raise ValueError("LINK_DENIED")
                    if stat.S_ISDIR(metadata.st_mode):
                        visit(item.path)
                    elif stat.S_ISREG(metadata.st_mode):
                        links = metadata.st_nlink or Path(item.path).stat().st_nlink
                        if links != 1:
                            raise ValueError("HARDLINK_DENIED")
                        count, size = count + 1, size + metadata.st_size
                        if count > 50000 or size > 2147483648:
                            raise ValueError("WORKSPACE_TOO_LARGE")
                        relative = Path(item.path).relative_to(base).as_posix()
                        manifest.update(relative.encode() + b"\0" + hashlib.sha256(Path(item.path).read_bytes()).digest())
                    else:
                        raise ValueError("SPECIAL_FILE_DENIED")
            visit(base)
        return manifest.hexdigest()
