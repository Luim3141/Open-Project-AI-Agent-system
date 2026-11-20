"""Bounded local process locks; Main ingestion runs only in the Linux Gateway."""
from contextlib import contextmanager
import os
from pathlib import Path
import time


@contextmanager
def lease(path, timeout=5.0):
    with Path(path).open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            if stream.seek(0,os.SEEK_END) == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            lock = lambda: msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            unlock = lambda: msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            lock = lambda: fcntl.flock(stream,fcntl.LOCK_EX | fcntl.LOCK_NB)
            unlock = lambda: fcntl.flock(stream,fcntl.LOCK_UN)
        start = time.monotonic()
        while True:
            try:
                lock()
                break
            except OSError:
                if time.monotonic() - start >= timeout:
                    raise ValueError('KNOWLEDGE_BUSY_RETRY_LATER') from None
                time.sleep(0.1)
        try:
            yield
        finally:
            try:
                unlock()
            except OSError:
                pass
