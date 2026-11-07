"""Process coordination and verification, independent of CLI and app UI."""
import contextlib
import fcntl
import os
import time
from pathlib import Path


def cache_dir():
    default = Path.home() / 'Library/Caches/bluebird-cli'
    return Path(os.environ.get('BLUEBIRD_CLI_HOME', default)).expanduser().resolve()


def wait_for(read, predicate, description, timeout=8):
    deadline = time.monotonic() + timeout
    while True:
        result = read()
        if predicate(result):
            return result
        if time.monotonic() >= deadline:
            raise RuntimeError(f'UNVERIFIED: {description}. The action may have happened; read state before retrying.')
        time.sleep(0.2)


@contextlib.contextmanager
def mutation_lock():
    cache_dir().mkdir(parents=True, exist_ok=True)
    with (cache_dir() / 'mutation.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another Bluebird CLI mutation is running; retry after it finishes')
        yield
