"""macOS process/Accessibility transport; contains no Bluebird UI workflow."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .runtime import cache_dir, mutation_lock

BUNDLE_ID = 'com.cub-and-pup.Bluebird'
SOURCE = Path(__file__).resolve().parent / 'native/ax.swift'


def helper_path():
    return cache_dir() / 'bluebird-ax'


class Bridge:
    def call(self, op, **kwargs):
        helper = helper_path()
        if not helper.is_file():
            raise RuntimeError('Accessibility helper missing. Run bluebird --full-access setup first.')
        stamp = helper.with_suffix('.sha256')
        digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        if not stamp.exists() or stamp.read_text().strip() != digest:
            raise RuntimeError('Native helper is outdated. Run bluebird --full-access setup after upgrading the CLI.')
        proc = subprocess.run([str(helper)], input=json.dumps({'op': op, **kwargs}),
                              capture_output=True, text=True, timeout=15)
        try:
            result = json.loads(proc.stdout)
        except ValueError:
            raise RuntimeError(proc.stderr.strip() or 'Accessibility helper returned invalid JSON')
        if proc.returncode or 'error' in result:
            raise RuntimeError(result.get('error', proc.stderr))
        return result

    def snapshot(self):
        return self.call('snapshot')['nodes']

    def open(self, url):
        if sys.platform != 'darwin':
            raise RuntimeError('macOS is required')
        proc = subprocess.run(['/usr/bin/open', '-b', BUNDLE_ID, url],
                              capture_output=True, text=True, timeout=15)
        if proc.returncode:
            raise RuntimeError(proc.stderr.strip() or 'Could not open Bluebird')

    def resources(self, app_path=None):
        from .localization import STRINGS
        request = {'keys': sorted({key for key, _ in STRINGS.values()})}
        if app_path is not None:
            request['app_path'] = str(app_path)
        return self.call('resources', **request)


def setup():
    if sys.platform != 'darwin':
        raise RuntimeError('Building the native helper requires macOS')
    with mutation_lock():
        helper = helper_path()
        staged = helper.with_suffix('.tmp')
        result = subprocess.run(['swiftc', '-module-cache-path', str(cache_dir() / 'module-cache'),
                                 str(SOURCE), '-o', str(staged)], capture_output=True, text=True, timeout=240)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or 'Native helper build failed')
        staged.replace(helper)
        helper.with_suffix('.sha256').write_text(hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    return {'helper': str(helper), **Bridge().call('doctor')}
