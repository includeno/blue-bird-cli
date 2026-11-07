import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from bluebird_cli.application import Application
from bluebird_cli.auth import AccessDenied, Authority, PERMISSIONS
from bluebird_cli.cli import main, parser
from bluebird_cli.store import DEFAULT_DB


class FakeStore:
    path = DEFAULT_DB.resolve()

    def __init__(self):
        self.available = [{'id': '101', 'name': 'Work'}, {'id': '102', 'name': 'Study'}, {'id': '103', 'name': 'Private'}]
        self.items = [dict(id=str(i), title=f'task {i}', status='active', notes='', duration=5, priority=0,
                           tags=[tag['name'] for tag in self.available if tag['id'] in ids], tag_ids=ids)
                      for i, ids in enumerate([['101'], ['101', '102'], ['101', '103'], ['103'], []], 1)]
        self.state = {'source': 'local_store', 'state': 'focusing', 'task_id': '1', 'duration': 5,
                      'remaining_seconds': 60, 'values': {'private_setting': 'hidden'}}

    def tasks(self, status='active', search=None):
        return copy.deepcopy([t for t in self.items if (status == 'all' or t['status'] == status)
                              and (not search or search.casefold() in t['title'].casefold())])

    def get(self, task_id):
        for item in self.items:
            if item['id'] == task_id:
                return copy.deepcopy(item)
        raise ValueError('Task not found')

    def tags(self):
        return copy.deepcopy(self.available)

    def timer(self):
        return copy.deepcopy(self.state)

    def logs(self, task_id=None):
        return [{'id': str(i), 'task_id': value, 'duration': 1} for i, value in enumerate(['1','2','3','4','5',None])
                if task_id is None or value == task_id]


class AuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.authority = Authority(Path(self.tmp.name) / 'auth.sqlite3')
        self.store = FakeStore()
        self.grant = self.authority.create('Agent', ['101','102'], sorted(PERMISSIONS), self.store.tags())
        self.bridge = Mock()
        self.bridge.resources.return_value = {'localizations': {'en': {}}, 'preferred_localizations': ['en']}
        self.app = Application(self.store, self.bridge, code=self.grant['code'], authority=self.authority)
        self.environment = patch.dict('os.environ', {'BLUEBIRD_CLI_HOME': self.tmp.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def run_command(self, *args):
        return self.app.execute(parser().parse_args(args))

    def test_secrets_not_stored_or_listed_and_scope_cannot_be_empty(self):
        self.assertNotIn(self.grant['code'], json.dumps(self.authority.list()))
        self.assertNotIn(self.grant['code'].encode(), self.authority.path.read_bytes())
        self.assertEqual(self.authority.path.stat().st_mode & 0o777, 0o600)
        for ids in ([], ['unknown'], '101', [101]):
            with self.assertRaises(ValueError): self.authority.create('name', ids, sorted(PERMISSIONS), self.store.tags())
        with self.assertRaises(ValueError): self.authority.update(self.grant['id'], 'name', [], sorted(PERMISSIONS), self.store.tags())

    def test_function_permissions_are_independent_of_tags(self):
        self.authority.update(self.grant['id'], 'Read only', ['101','102'], ['list','get'], self.store.tags())
        self.assertEqual(len(self.run_command('list')), 2)
        self.assertEqual(self.run_command('auth-status')['permissions'], ['get','list'])
        for args in (['tags'], ['logs'], ['add','x','--tags','Work','--dry-run'],
                     ['update','1','--notes','x','--dry-run'], ['delete','1','--yes'],
                     ['complete','1'], ['reopen','1'], ['timer','status']):
            with self.subTest(args=args), self.assertRaisesRegex(AccessDenied, 'CLI function'):
                self.run_command(*args)
        self.authority.update(self.grant['id'], 'Create only', ['101'], ['add'], self.store.tags())
        self.assertEqual(self.run_command('add','x','--tags','Work','--dry-run')['status'], 'preview')
        with self.assertRaises(AccessDenied): self.run_command('list')
        self.assertFalse(self.bridge.mock_calls)

    def test_permissions_rechecked_after_waiting_for_mutation_lock(self):
        @contextlib.contextmanager
        def changed_while_waiting():
            self.authority.update(self.grant['id'], 'Now read only', ['101'], ['get'], self.store.tags())
            yield
        with patch('bluebird_cli.application.mutation_lock', changed_while_waiting):
            with self.assertRaisesRegex(AccessDenied, 'CLI function'):
                self.run_command('update','1','--notes','forbidden')
        self.assertFalse(self.bridge.mock_calls)

    def test_timer_actions_are_separately_granted(self):
        self.authority.update(self.grant['id'], 'Timer observer', ['101'], ['timer.status'], self.store.tags())
        self.assertEqual(self.run_command('timer','status')['task_id'], '1')
        for action in ('start','stop','finish','reset'):
            args = ['timer',action,'--dry-run'] + (['--task','1'] if action == 'start' else [])
            with self.subTest(action=action), self.assertRaisesRegex(AccessDenied, 'CLI function'):
                self.run_command(*args)
        self.assertFalse(self.bridge.mock_calls)

    def test_invalid_function_grants_and_legacy_migration(self):
        for permissions in ([], None, 'list', ['web'], ['unknown'], [1]):
            with self.subTest(permissions=permissions), self.assertRaises(ValueError):
                self.authority.create('Invalid', ['101'], permissions, self.store.tags())
        import sqlite3
        with sqlite3.connect(self.authority.path) as db:
            rows = db.execute('SELECT id,digest,label,tags,created_at,revoked_at FROM grants').fetchall()
            db.execute('DROP TABLE grants')
            db.execute('CREATE TABLE grants (id TEXT PRIMARY KEY,digest TEXT,label TEXT,tags TEXT,created_at TEXT,revoked_at TEXT)')
            db.executemany('INSERT INTO grants VALUES (?,?,?,?,?,?)', rows)
        self.assertEqual(self.run_command('auth-status')['permissions'], [])
        with self.assertRaisesRegex(AccessDenied, 'CLI function'): self.run_command('list')

    def test_label_lengths_types_and_duplicate_grants(self):
        before=self.authority.list()
        for label in (None, False, 12, [], {}, '', ' \t\n', '界'*81):
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.authority.create(label, ['101'], ['get'], self.store.tags())
        self.assertEqual(self.authority.list(), before)
        for label in ('界', '界'*80):
            grant=self.authority.create('  '+label+'  ', ['102','101','101'], ['get','list','get'], self.store.tags())
            self.assertEqual(grant['label'], label)
            self.assertEqual([tag['id'] for tag in grant['tags']], ['101','102'])
            self.assertEqual(grant['permissions'], ['get','list'])

    def test_invalid_updates_leave_existing_grant_unchanged(self):
        before=self.authority.list()
        for label, tags, permissions in (('', ['101'], ['get']), ('ok', [], ['get']),
                                         ('ok', ['missing'], ['get']), ('ok', ['101'], []),
                                         ('ok', ['101'], ['start web'])):
            with self.subTest(label=label,tags=tags,permissions=permissions), self.assertRaises(ValueError):
                self.authority.update(self.grant['id'], label, tags, permissions, self.store.tags())
            self.assertEqual(self.authority.list(), before)
        with self.assertRaises(ValueError):
            self.authority.update('0'*24, 'missing', ['101'], ['get'], self.store.tags())
        with self.assertRaises(ValueError): self.authority.revoke('0'*24)
        self.assertEqual(self.authority.list(), before)

    def test_code_persistence_invalid_values_and_idempotent_revocation(self):
        reopened=Authority(self.authority.path)
        self.assertEqual(reopened.resolve(self.grant['code']).grant_id, self.grant['id'])
        for code in (None, 1, '', 'bb_', 'BB_abc', 'bb_'+'x'*126, 'bb_未知', ' '+self.grant['code'], self.grant['code']+'x'):
            with self.subTest(code=code), self.assertRaises(AccessDenied): reopened.resolve(code)
        first=reopened.revoke(self.grant['id'])
        with patch('bluebird_cli.auth.now', return_value='later'):
            self.assertEqual(reopened.revoke(self.grant['id']), first)
        with self.assertRaises(AccessDenied): self.authority.resolve(self.grant['code'])
        self.assertNotIn('code', first)
        self.assertNotIn('digest', first)

    def test_all_fourteen_functions_require_their_own_grant(self):
        commands={
            'list':['list'], 'get':['get','1'], 'tags':['tags'], 'logs':['logs'],
            'add':['add','new','--tags','Work','--dry-run'],
            'update':['update','1','--notes','new','--dry-run'],
            'complete':['complete','1','--dry-run'], 'reopen':['reopen','1','--dry-run'],
            'delete':['delete','1','--dry-run'], 'timer.status':['timer','status'],
            'timer.start':['timer','start','--task','1','--dry-run'],
            'timer.stop':['timer','stop','--dry-run'], 'timer.finish':['timer','finish','--dry-run'],
            'timer.reset':['timer','reset','--dry-run'],
        }
        self.assertEqual(set(commands), set(PERMISSIONS))
        for permission, argv in commands.items():
            with self.subTest(permission=permission):
                self.authority.update(self.grant['id'], 'Single function', ['101'], [permission], self.store.tags())
                self.run_command(*argv)
                self.authority.update(self.grant['id'], 'Other functions', ['101'], sorted(PERMISSIONS-{permission}), self.store.tags())
                with self.assertRaisesRegex(AccessDenied, 'CLI function'): self.run_command(*argv)
        self.assertFalse(self.bridge.mock_calls)

    def test_scope_changes_and_revocation_while_waiting_for_lock(self):
        for change in ('scope','revoke'):
            with self.subTest(change=change):
                @contextlib.contextmanager
                def changed_while_waiting():
                    if change=='scope':
                        self.authority.update(self.grant['id'], 'Study', ['102'], sorted(PERMISSIONS), self.store.tags())
                    else:self.authority.revoke(self.grant['id'])
                    yield
                self.authority.update(self.grant['id'], 'Work', ['101'], sorted(PERMISSIONS), self.store.tags())
                with patch('bluebird_cli.application.mutation_lock', changed_while_waiting):
                    with self.assertRaises(AccessDenied): self.run_command('update','1','--notes','no')
        self.assertFalse(self.bridge.mock_calls)

    def test_changed_task_scope_and_timer_target_before_ui_write(self):
        for argv in (['update','1','--notes','no'], ['timer','stop']):
            with self.subTest(argv=argv):
                self.store.items[0]['tag_ids']=['101']
                self.store.state['task_id']='1'
                adapter=Mock()
                def changed_after_preflight():
                    if argv[0]=='update':self.store.items[0]['tag_ids']=['103']
                    else:self.store.state['task_id']='4'
                adapter.snapshot.side_effect=changed_after_preflight
                with patch('bluebird_cli.application.BluebirdUI', return_value=adapter):
                    with self.assertRaises(AccessDenied): self.run_command(*argv)
                adapter.edit_task.assert_not_called()
                adapter.end_timer.assert_not_called()

    def test_timer_idle_missing_and_unknown_targets_are_redacted(self):
        for state, task_id in (('idle',None), ('idle','999'), ('focusing',None), ('finished','999'), ('break','4')):
            with self.subTest(state=state,task_id=task_id):
                self.store.state.update(state=state,task_id=task_id)
                expected={'source':'local_store','state':'unavailable'}
                if state=='idle' and task_id is None:expected={'source':'local_store','state':'idle','task_id':None}
                self.assertEqual(self.run_command('timer','status'), expected)
                for action in ('stop','finish','reset'):
                    with self.assertRaises(AccessDenied): self.run_command('timer',action)
        self.assertFalse(self.bridge.mock_calls)

    def test_explicit_code_and_full_access_override_environment(self):
        restricted=self.authority.create('Study', ['102'], ['list'], self.store.tags())
        with patch('bluebird_cli.cli.Store', return_value=self.store), patch('bluebird_cli.application.Authority', return_value=self.authority):
            for argv, env, expected_status, expected_ids in (
                (['--code',self.grant['code'],'list'], restricted['code'], 0, ['1','2']),
                (['--code','','list'], self.grant['code'], 3, None),
                (['--full-access','list'], 'invalid', 0, ['1','2','3','4','5']),
                (['list'], 'invalid', 3, None),
                (['capabilities'], 'invalid', 0, None),
            ):
                with self.subTest(argv=argv), patch.dict('os.environ', {'BLUEBIRD_CODE':env}), contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(main(argv), expected_status)
                result=json.loads(out.getvalue())
                if expected_ids is not None:self.assertEqual([task['id'] for task in result['data']],expected_ids)
                if expected_status:self.assertEqual(result['error']['code'],'access_denied')

    def test_read_scope_uses_all_nonempty_tags(self):
        self.assertEqual([t['id'] for t in self.run_command('list')], ['1','2'])
        self.assertEqual(self.run_command('list','--search','task 3'), [])
        self.assertEqual([t['id'] for t in self.run_command('tags')], ['101','102'])
        for task_id in ('3','4','5','999999'):
            with self.assertRaisesRegex(AccessDenied, 'Task unavailable'):
                self.run_command('get', task_id)
        self.assertEqual([log['task_id'] for log in self.run_command('logs')], ['1','2'])
        with self.assertRaises(AccessDenied): self.run_command('logs','--task','4')

    def test_rename_does_not_expand_scope_to_recreated_tag(self):
        self.store.available[0]['name'] = 'Renamed'
        self.store.items[0]['tags'] = ['Renamed']
        self.assertEqual(self.run_command('get','1')['id'], '1')
        self.store.available.append({'id':'104','name':'Work'})
        self.store.items[0].update(tags=['Work'], tag_ids=['104'])
        with self.assertRaises(AccessDenied): self.run_command('get','1')
        with self.assertRaises(AccessDenied): self.run_command('add','new','--tags','Work','--dry-run')

    def test_write_and_preview_denied_before_any_ui(self):
        commands = [ ['update','3','--notes','x'], ['complete','3'], ['reopen','4'], ['delete','4','--yes'],
                     ['update','1','--tags',''], ['update','1','--tags','Work,Private'], ['add','new'],
                     ['add','new','--tags','Unknown'], ['add','new','--tags','Work,Private'],
                     ['timer','start','--task','4'], ['ui'], ['doctor'], ['setup'], ['open'], ['focus'], ['start','web'] ]
        for args in commands:
            with self.subTest(args=args), self.assertRaises(AccessDenied): self.run_command(*args)
        for args in (['delete','4','--dry-run'], ['update','1','--tags','','--dry-run'], ['timer','start','--task','4','--dry-run']):
            with self.assertRaises(AccessDenied): self.run_command(*args)
        self.assertFalse(self.bridge.mock_calls)

    def test_valid_preview_never_exposes_code(self):
        args = parser().parse_args(['--code', self.grant['code'], 'add','new','--tags','Work','--dry-run'])
        result = self.app.execute(args)
        self.assertEqual(result['status'], 'preview')
        self.assertNotIn(self.grant['code'], json.dumps(result))
        self.assertFalse(self.bridge.mock_calls)

    def test_allowed_mutation_and_revocation_before_next_command(self):
        ui = Mock()
        def edit(task, expected): self.store.items[0].update(expected)
        ui.edit_task.side_effect = edit
        with patch('bluebird_cli.application.BluebirdUI', return_value=ui):
            self.assertEqual(self.run_command('update','1','--notes','allowed')['notes'], 'allowed')
        self.authority.update(self.grant['id'], 'Study only', ['102'], sorted(PERMISSIONS), self.store.tags())
        self.assertEqual(self.run_command('list'), [])
        self.authority.revoke(self.grant['id'])
        for args in (['list'], ['auth-status'], ['add','x','--tags','Study','--dry-run']):
            with self.assertRaises(AccessDenied): self.run_command(*args)
        with self.assertRaises(ValueError): self.authority.update(self.grant['id'], 'revived', ['101'], sorted(PERMISSIONS), self.store.tags())

    def test_timer_redaction_and_foreign_controls(self):
        self.assertNotIn('values', self.run_command('timer','status'))
        self.store.state['task_id'] = '4'
        self.assertEqual(self.run_command('timer','status'), {'source':'local_store','state':'unavailable'})
        for action in ('stop','finish','reset'):
            with self.assertRaises(AccessDenied): self.run_command('timer',action)
        self.assertFalse(self.bridge.mock_calls)

    def test_code_cannot_substitute_database(self):
        self.store.path = Path(self.tmp.name) / 'other.sqlite'
        with self.assertRaises(AccessDenied): self.run_command('list')
        with self.assertRaises(AccessDenied): self.run_command('add','new','--tags','Work','--dry-run')

    def test_duplicate_tag_names_cannot_target_other_id(self):
        self.store.available.append({'id': '999', 'name': 'Work'})
        with self.assertRaises(AccessDenied): self.run_command('add','new','--tags','Work','--dry-run')

    def test_full_access_retains_unrestricted_reads(self):
        app = Application(self.store, full_access=True)
        self.assertEqual(len(app.execute(parser().parse_args(['list']))), 5)
        self.assertEqual(app.execute(parser().parse_args(['timer','status'])), self.store.state)

    def test_start_web_owner_entrypoint_and_code_rejection(self):
        with patch('bluebird_cli.cli.Store', return_value=self.store), patch('bluebird_cli.web.serve', return_value={'status':'stopped'}) as serve:
            with patch.dict('os.environ', {'BLUEBIRD_CODE':''}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['start','web']), 0)
                self.assertEqual(serve.call_args.args[2], 8765)
                self.assertEqual(main(['start','web','--port','0']), 0)
                self.assertEqual(serve.call_args.args[2], 0)
                self.assertEqual(main(['start']), 2)
                self.assertEqual(main(['start','web','--port','65536']), 2)
                self.assertEqual(main(['--full-access','web']), 2)
            serve.reset_mock()
            for argv, environment in ((['--code',self.grant['code'],'start','web'], ''),
                                      (['start','web'], self.grant['code'])):
                with patch.dict('os.environ', {'BLUEBIRD_CODE':environment}), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(argv), 3)
            serve.assert_not_called()
            with patch.dict('os.environ', {'BLUEBIRD_CODE':''}), contextlib.redirect_stdout(io.StringIO()):
                self.store.path=Path(self.tmp.name)/'snapshot.sqlite'
                self.assertEqual(main(['start','web']), 2)
            serve.assert_not_called()
        capabilities=Application().execute(parser().parse_args(['capabilities']))
        self.assertIn('start web', capabilities['commands'])
        self.assertNotIn('web', capabilities['commands'])

    def test_cli_requires_mode_accepts_env_and_returns_exit_3(self):
        with patch('bluebird_cli.cli.Store', return_value=self.store), patch('bluebird_cli.application.Authority', return_value=self.authority):
            with patch.dict('os.environ', {'BLUEBIRD_CODE':''}), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(['list']),3)
                self.assertEqual(json.loads(out.getvalue())['error']['code'],'access_denied')
            with patch.dict('os.environ', {'BLUEBIRD_CODE':self.grant['code']}), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(['list']),0)
                self.assertEqual(len(json.loads(out.getvalue())['data']),2)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--full-access','--code',self.grant['code'],'list']),2)


if __name__ == '__main__': unittest.main()
