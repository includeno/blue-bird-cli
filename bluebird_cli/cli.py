"""Control the Bluebird macOS app. JSON is the default output format."""
import argparse
import json
import os
import sqlite3
import subprocess
from pathlib import Path

from . import __version__
from .application import Application
from .auth import AccessDenied
from .store import Store, DEFAULT_DB
from .url_scheme import nonempty, positive_minutes


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def parser():
    p = Parser(description=__doc__)
    p.add_argument('--version', action='version', version=f'bluebird {__version__}')
    p.add_argument('--db', type=Path, default=DEFAULT_DB, help='Read-only database path (writes require the default live store)')
    p.add_argument('--locale', default='auto', help='App UI locale: auto-detect, or a locale reported by locales')
    access = p.add_mutually_exclusive_group()
    access.add_argument('--full-access', action='store_true', help='Local owner mode: unrestricted access')
    access.add_argument('--code', help='Function- and tag-scoped authorization code (or set BLUEBIRD_CODE)')
    commands = p.add_subparsers(dest='command', required=True)
    for name in ('setup', 'doctor', 'capabilities', 'ui', 'locales', 'tags', 'auth-status'):
        commands.add_parser(name)
    start = commands.add_parser('start', help='Start a local service')
    services = start.add_subparsers(dest='service', required=True)
    web = services.add_parser('web', help='Start the local owner console; no access flag needed')
    web.add_argument('--port', type=port_number, default=8765, help='Loopback port; 0 selects a free port')
    for name in ('open', 'focus'):
        commands.add_parser(name).add_argument('--dry-run', action='store_true')
    add = commands.add_parser('add', help='Create a task and return its verified ID')
    add.add_argument('title', type=nonempty)
    fields(add)
    add.add_argument('--dry-run', action='store_true')
    ls = commands.add_parser('list', help='Read all matching tasks, including off-screen tasks')
    ls.add_argument('--status', choices=('active','completed','deleted','all'), default='active')
    ls.add_argument('--search')
    for name in ('get', 'update', 'complete', 'reopen', 'delete'):
        c = commands.add_parser(name)
        c.add_argument('id', type=task_id)
        if name == 'update':
            c.add_argument('--title', type=nonempty)
            fields(c, allow_clear=True)
        if name in ('update','complete','reopen','delete'):
            c.add_argument('--dry-run', action='store_true')
        if name == 'delete':
            c.add_argument('--yes', action='store_true', help='Required for unattended deletion of this exact ID')
    timer = commands.add_parser('timer')
    timers = timer.add_subparsers(dest='action', required=True)
    for name in ('status','start','stop','finish','reset'):
        t = timers.add_parser(name)
        if name == 'start':
            t.add_argument('--task', type=task_id, required=True)
            t.add_argument('--duration', type=session_minutes, help='Session minutes, a multiple of 5 (5..600)')
        if name != 'status':
            t.add_argument('--dry-run', action='store_true')
    logs = commands.add_parser('logs')
    logs.add_argument('--task', type=task_id)
    return p


def port_number(value):
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('port must be between 0 and 65535')
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError('port must be between 0 and 65535')
    return port


def task_id(value):
    if not value.isascii() or not value.isdigit():
        raise argparse.ArgumentTypeError('id must be the numeric string returned by list/add')
    return value


def session_minutes(value):
    minutes = positive_minutes(value)
    if minutes % 5 or minutes > 600:
        raise argparse.ArgumentTypeError('timer duration must be a multiple of 5, between 5 and 600; Bluebird UI uses 5-minute steps')
    return minutes


def clearable_minutes(value):
    if value == '0': return 0
    return positive_minutes(value)


def fields(p, allow_clear=False):
    p.add_argument('--notes')
    p.add_argument('--duration', type=clearable_minutes if allow_clear else positive_minutes)
    p.add_argument('--priority', choices=('none','low','medium','high') if allow_clear else ('low','medium','high'))
    p.add_argument('--tags', help='Comma-separated tags; empty string clears tags on update')


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        code = args.code if args.code is not None else (None if args.full_access else (os.environ.get('BLUEBIRD_CODE') or None))
        result = Application(Store(args.db), locale=args.locale, full_access=args.full_access, code=code).execute(args)
        print(json.dumps({'ok': True, 'data': result}, ensure_ascii=False, allow_nan=False))
        return 0
    except AccessDenied as e:
        code, status, message = 'access_denied', 3, str(e)
    except (ValueError, argparse.ArgumentTypeError) as e:
        code, status, message = 'invalid_argument', 2, str(e)
    except (OSError, RuntimeError, sqlite3.Error, subprocess.SubprocessError) as e:
        code, status, message = 'operation_failed', 1, str(e)
    print(json.dumps({'ok': False, 'error': {'code': code, 'message': message}}, ensure_ascii=False))
    return status
