"""Local authorization codes and task scopes, independent of HTTP and CLI parsing."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
from datetime import datetime, timezone

DEFAULT_AUTH_DB = Path.home() / 'Library/Application Support/bluebird-cli/authorization.sqlite3'
PUBLIC_COMMANDS = {'capabilities', 'locales'}
ADMIN_COMMANDS = {'setup', 'doctor', 'ui', 'open', 'focus', 'start web'}
PERMISSION_GROUPS = {
    'read': ['list', 'get', 'tags', 'logs'],
    'tasks': ['add', 'update', 'complete', 'reopen', 'delete'],
    'timer': ['timer.status', 'timer.start', 'timer.stop', 'timer.finish', 'timer.reset'],
}
PERMISSIONS = frozenset(item for group in PERMISSION_GROUPS.values() for item in group)


class AccessDenied(RuntimeError):
    pass


class Access:
    def __init__(self, tag_ids=None, grant_id=None, permissions=()):
        self.full = tag_ids is None
        self.tag_ids = frozenset(tag_ids or ())
        self.grant_id = grant_id
        self.permissions = frozenset(permissions)

    def require_command(self, args):
        permission = f'timer.{args.action}' if args.command == 'timer' else args.command
        if not self.full and permission != 'auth-status' and permission not in self.permissions:
            raise AccessDenied(f'Code does not permit CLI function: {permission}')

    def allows(self, task):
        tags = set(task.get('tag_ids', []))
        return self.full or bool(tags) and tags <= self.tag_ids

    def require_task(self, task):
        if not self.allows(task):
            raise AccessDenied('Task unavailable in this code scope')
        return task

    def validate_tags(self, value, store):
        if self.full:
            return
        names = {name.strip() for name in (value or '').split(',') if name.strip()}
        if not names:
            raise AccessDenied('Code mode requires at least one authorized tag; tags cannot be cleared')
        tags = store.tags()
        for name in names:
            found = [tag for tag in tags if tag['name'] == name]
            if len(found) != 1 or found[0]['id'] not in self.tag_ids:
                raise AccessDenied('Tags must uniquely identify existing authorized tags; new tags require full-access')

    def timer_view(self, state, store):
        if self.full:
            return state
        task_id = state.get('task_id')
        if task_id is None and state['state'] == 'idle':
            return {'source': 'local_store', 'state': 'idle', 'task_id': None}
        try:
            task = store.get(task_id)
        except ValueError:
            task = None
        if task is None or not self.allows(task):
            return {'source': 'local_store', 'state': 'unavailable'}
        return {key: value for key, value in state.items() if key != 'values'}


def now():
    return datetime.now(timezone.utc).isoformat()


class Authority:
    def __init__(self, path=DEFAULT_AUTH_DB):
        self.path = Path(path)

    def connect(self):
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.path.chmod(0o600)
        db = sqlite3.connect(self.path, timeout=3)
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE IF NOT EXISTS grants ('
                   'id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL, label TEXT NOT NULL, '
                   'tags TEXT NOT NULL, created_at TEXT NOT NULL, revoked_at TEXT, permissions TEXT NOT NULL)')
        if 'permissions' not in {row['name'] for row in db.execute('PRAGMA table_info(grants)')}:
            # Older grants get no function privileges until the owner explicitly assigns them.
            db.execute("ALTER TABLE grants ADD COLUMN permissions TEXT NOT NULL DEFAULT '[]'")
        db.commit()
        return db

    @staticmethod
    def validate(label, tag_ids, permissions, available):
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 80:
            raise ValueError('Label must contain 1 to 80 characters')
        if not isinstance(tag_ids, list) or not tag_ids or any(not isinstance(i, str) for i in tag_ids):
            raise ValueError('Select at least one tag ID')
        if (not isinstance(permissions, list) or not permissions
                or any(not isinstance(item, str) or item not in PERMISSIONS for item in permissions)):
            raise ValueError('Select at least one supported CLI function')
        by_id = {tag['id']: tag for tag in available}
        if not set(tag_ids) <= by_id.keys():
            raise ValueError('One or more selected tags no longer exist; refresh the tag list')
        return label.strip(), [by_id[i] for i in sorted(set(tag_ids))], sorted(set(permissions))

    @staticmethod
    def record(row):
        return {key: json.loads(row[key]) if key in ('tags', 'permissions') else row[key]
                for key in ('id', 'label', 'tags', 'permissions', 'created_at', 'revoked_at')}

    def list(self):
        db = self.connect()
        try:
            return [self.record(row) for row in db.execute('SELECT * FROM grants ORDER BY created_at DESC')]
        finally:
            db.close()

    def create(self, label, tag_ids, permissions, available):
        label, tags, permissions = self.validate(label, tag_ids, permissions, available)
        code = 'bb_' + secrets.token_urlsafe(32)
        grant_id = secrets.token_hex(12)
        db = self.connect()
        try:
            with db:
                db.execute('INSERT INTO grants (id,digest,label,tags,created_at,revoked_at,permissions) VALUES (?,?,?,?,?,NULL,?)',
                           (grant_id, hashlib.sha256(code.encode()).hexdigest(), label, json.dumps(tags), now(), json.dumps(permissions)))
            row = db.execute('SELECT * FROM grants WHERE id=?', (grant_id,)).fetchone()
            return {**self.record(row), 'code': code}
        finally:
            db.close()

    def update(self, grant_id, label, tag_ids, permissions, available):
        label, tags, permissions = self.validate(label, tag_ids, permissions, available)
        db = self.connect()
        try:
            with db:
                result = db.execute('UPDATE grants SET label=?,tags=?,permissions=? WHERE id=? AND revoked_at IS NULL',
                                    (label, json.dumps(tags), json.dumps(permissions), grant_id))
                if result.rowcount != 1:
                    raise ValueError('Active code not found')
            return self.record(db.execute('SELECT * FROM grants WHERE id=?', (grant_id,)).fetchone())
        finally:
            db.close()

    def revoke(self, grant_id):
        db = self.connect()
        try:
            with db:
                result = db.execute('UPDATE grants SET revoked_at=COALESCE(revoked_at,?) WHERE id=?', (now(), grant_id))
                if result.rowcount != 1:
                    raise ValueError('Code not found')
            return self.record(db.execute('SELECT * FROM grants WHERE id=?', (grant_id,)).fetchone())
        finally:
            db.close()

    def resolve(self, code):
        if not isinstance(code, str) or not code.startswith('bb_') or len(code) > 128:
            raise AccessDenied('Invalid or revoked authorization code')
        db = self.connect()
        try:
            row = db.execute('SELECT * FROM grants WHERE digest=? AND revoked_at IS NULL',
                             (hashlib.sha256(code.encode()).hexdigest(),)).fetchone()
            if row is None:
                raise AccessDenied('Invalid or revoked authorization code')
            tags = json.loads(row['tags'])
            if not tags:
                raise AccessDenied('Authorization code has no tag scope')
            return Access([tag['id'] for tag in tags], row['id'], json.loads(row['permissions']))
        finally:
            db.close()
