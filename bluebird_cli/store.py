"""Read Bluebird's local Core Data store; never write application data."""
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / 'Library/Group Containers/group.com.cub-and-pup.Bluebird/Bluebird.sqlite'
EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def iso(value):
    return (EPOCH + timedelta(seconds=value)).isoformat() if value is not None else None


class Store:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path).expanduser().resolve()

    def connect(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=3)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        # shortcut: verified against Bluebird 3.14.1; update the reader when its Core Data schema changes.
        required = {'ZTASK': {'Z_PK', 'ZID', 'ZTITLE', 'ZNOTES', 'ZDURATION', 'ZPRIORITY',
                               'ZSTARTDATE', 'ZDUEDATE', 'ZCOMPLETIONDATE', 'ZDELETIONDATE',
                               'ZMODIFICATIONDATE', 'ZRECURRENCERULE'},
                    'ZTAG': {'Z_PK', 'ZID', 'ZNAME', 'ZDELETIONDATE'},
                    'Z_4TASKS': {'Z_4TAGS', 'Z_5TASKS'}, 'ZPAIR': {'ZKEY', 'ZVALUE'},
                    'ZFOCUSLOG': {'ZID', 'ZTASK', 'ZDURATION', 'ZDELETIONDATE'}}
        for table, columns in required.items():
            actual = {row['name'] for row in db.execute(f'PRAGMA table_info({table})')}
            if not columns <= actual:
                db.close()
                raise RuntimeError(f'Unsupported Bluebird database schema: {table}')
        return db

    def tasks(self, status='active', search=None):
        db = self.connect()
        try:
            db.execute('BEGIN')
            tags = {}
            for row in db.execute('SELECT j.Z_5TASKS, t.ZNAME, t.ZID FROM Z_4TASKS j JOIN ZTAG t '
                                  'ON t.Z_PK=j.Z_4TAGS WHERE t.ZDELETIONDATE IS NULL ORDER BY t.ZNAME'):
                tags.setdefault(row[0], []).append((row[1], str(row[2])))
            result = []
            for r in db.execute('SELECT * FROM ZTASK ORDER BY ZID'):
                state = 'deleted' if r['ZDELETIONDATE'] is not None else (
                    'completed' if r['ZCOMPLETIONDATE'] is not None else 'active')
                if status != 'all' and status != state:
                    continue
                if search and search.casefold() not in (r['ZTITLE'] or '').casefold():
                    continue
                result.append({'id': str(r['ZID']), 'title': r['ZTITLE'] or '', 'notes': r['ZNOTES'] or '',
                               'duration': (r['ZDURATION'] or 0) / 60, 'priority': r['ZPRIORITY'] or 0,
                               'tags': [tag[0] for tag in tags.get(r['Z_PK'], [])],
                               'tag_ids': [tag[1] for tag in tags.get(r['Z_PK'], [])], 'status': state,
                               'start_date': iso(r['ZSTARTDATE']), 'due_date': iso(r['ZDUEDATE']),
                               'completed_at': iso(r['ZCOMPLETIONDATE']), 'deleted_at': iso(r['ZDELETIONDATE']),
                               'modified_at': iso(r['ZMODIFICATIONDATE']), 'recurrence': r['ZRECURRENCERULE']})
            return result
        finally:
            db.close()

    def get(self, task_id):
        matches = [t for t in self.tasks('all') if t['id'] == str(task_id)]
        if len(matches) != 1:
            raise ValueError(f'Task not found: {task_id}')
        return matches[0]

    def tags(self):
        db = self.connect()
        try:
            return [{'id': str(row['ZID']), 'name': row['ZNAME'] or ''}
                    for row in db.execute('SELECT ZID,ZNAME FROM ZTAG WHERE ZDELETIONDATE IS NULL ORDER BY ZNAME,ZID')]
        finally:
            db.close()

    def timer(self):
        db = self.connect()
        try:
            values = dict(db.execute("SELECT ZKEY,ZVALUE FROM ZPAIR WHERE ZKEY LIKE 'focus.%'"))
            state = 'break' if values.get('focus.breakStartDate') else ('focusing' if values.get('focus.sessionStartDate') else 'idle')
            end = values.get('focus.sessionEndDate' if state == 'focusing' else 'focus.breakEndDate')
            remaining = max(0, (EPOCH + timedelta(seconds=float(end)) - datetime.now(timezone.utc)).total_seconds()) if end else None
            if remaining == 0 and state != 'idle':
                state = 'finished' if state == 'focusing' else 'break_finished'
            return {'source': 'local_store', 'state': state, 'task_id': values.get('focus.selectedTaskID'),
                    'duration': float(values['focus.sessionDuration']) / 60 if values.get('focus.sessionDuration') else None,
                    'remaining_seconds': remaining, 'values': values}
        finally:
            db.close()

    def logs(self, task_id=None):
        db = self.connect()
        try:
            rows = db.execute('SELECT l.ZID,l.ZDURATION,t.ZID AS TASK_ID FROM ZFOCUSLOG l '
                              'LEFT JOIN ZTASK t ON t.Z_PK=l.ZTASK WHERE l.ZDELETIONDATE IS NULL ORDER BY l.ZID')
            return [{'id': str(r['ZID']), 'task_id': str(r['TASK_ID']) if r['TASK_ID'] is not None else None,
                     'duration': (r['ZDURATION'] or 0) / 60} for r in rows
                    if task_id is None or str(r['TASK_ID']) == str(task_id)]
        finally:
            db.close()
