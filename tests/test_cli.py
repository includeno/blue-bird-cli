import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from bluebird_cli import cli
from bluebird_cli.application import Application
from bluebird_cli.macos import Bridge
from bluebird_cli.runtime import wait_for, mutation_lock
from bluebird_cli.store import Store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'Bluebird.sqlite'
        db = sqlite3.connect(self.path)
        db.executescript('''
            CREATE TABLE ZTASK (Z_PK INTEGER PRIMARY KEY, ZID INTEGER, ZTITLE TEXT, ZNOTES TEXT,
              ZDURATION REAL, ZPRIORITY INTEGER, ZSTARTDATE REAL, ZDUEDATE REAL, ZCOMPLETIONDATE REAL,
              ZDELETIONDATE REAL, ZMODIFICATIONDATE REAL, ZRECURRENCERULE TEXT);
            CREATE TABLE ZTAG (Z_PK INTEGER, ZID INTEGER, ZNAME TEXT, ZDELETIONDATE REAL);
            CREATE TABLE Z_4TASKS (Z_4TAGS INTEGER, Z_5TASKS INTEGER);
            CREATE TABLE ZPAIR (ZKEY TEXT, ZVALUE TEXT);
            CREATE TABLE ZFOCUSLOG (ZID INTEGER, ZTASK INTEGER, ZDURATION REAL, ZDELETIONDATE REAL);
            INSERT INTO ZTASK VALUES(1,7705161843629854611,'中文 & test','notes',1500,3,NULL,NULL,NULL,NULL,0,NULL);
            INSERT INTO ZTASK VALUES(2,20,'same title','',0,0,NULL,NULL,1,NULL,2,NULL);
            INSERT INTO ZTASK VALUES(3,30,'same title','',0,0,NULL,NULL,NULL,2,3,NULL);
            INSERT INTO ZTAG VALUES(1,10,'工作',NULL);
            INSERT INTO ZTAG VALUES(2,11,'deleted tag',1);
            INSERT INTO Z_4TASKS VALUES(1,1);
            INSERT INTO Z_4TASKS VALUES(2,1);
            INSERT INTO ZFOCUSLOG VALUES(99,1,120,NULL);
            INSERT INTO ZPAIR VALUES('focus.selectedTaskID','7705161843629854611');
        ''')
        db.commit(); db.close()
        self.store = Store(self.path)

    def test_read_model(self):
        task = self.store.tasks()[0]
        self.assertEqual(task['id'], '7705161843629854611')
        self.assertEqual(task['duration'], 25)
        self.assertEqual(task['tags'], ['工作'])
        self.assertEqual(task['tag_ids'], ['10'])
        self.assertEqual(self.store.tags(), [{'id': '10', 'name': '工作'}])
        self.assertEqual(task['modified_at'], '2001-01-01T00:00:00+00:00')
        self.assertEqual(len(self.store.tasks('all')), 3)
        self.assertEqual(self.store.tasks('completed')[0]['id'], '20')
        self.assertEqual(self.store.tasks('deleted')[0]['id'], '30')
        self.assertEqual(self.store.tasks(search='TEST'), [task])
        self.assertEqual(self.store.get(task['id']), task)
        self.assertEqual(self.store.logs(task['id'])[0]['duration'], 2)
        with self.assertRaises(ValueError): self.store.get('missing')

    def test_finished_timer_and_break_precedence(self):
        db = sqlite3.connect(self.path)
        db.executemany('INSERT INTO ZPAIR VALUES (?,?)', [('focus.sessionStartDate','1'), ('focus.sessionEndDate','2')])
        db.commit()
        self.assertEqual(self.store.timer()['state'], 'finished')
        db.executemany('INSERT INTO ZPAIR VALUES (?,?)', [('focus.breakStartDate','3'), ('focus.breakEndDate','4')])
        db.commit(); db.close()
        self.assertEqual(self.store.timer()['state'], 'break_finished')
        self.assertEqual(self.store.timer()['remaining_seconds'], 0)

    def test_read_only_and_schema_detection(self):
        before = self.path.read_bytes()
        db = self.store.connect()
        with self.assertRaises(sqlite3.OperationalError): db.execute('DELETE FROM ZTASK')
        db.close()
        self.assertEqual(self.path.read_bytes(), before)
        other = Path(self.tmp.name) / 'missing.sqlite'
        with self.assertRaises(sqlite3.OperationalError): Store(other).tasks()
        self.assertFalse(other.exists())
        db = sqlite3.connect(self.path); db.execute('DROP TABLE ZTAG'); db.close()
        with self.assertRaisesRegex(RuntimeError, 'schema'): self.store.tasks()

    def test_cli_json_and_no_mutation_on_preview(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(['--full-access', '--db', str(self.path), 'list']), 0)
        self.assertEqual(json.loads(out.getvalue())['data'][0]['id'], '7705161843629854611')
        with patch.object(Bridge, 'open') as dispatch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--full-access', 'add','中文','--dry-run']), 0)
            self.assertEqual(cli.main(['--full-access', 'delete','20']), 2)
            self.assertEqual(cli.main(['--full-access', '--db',str(self.path),'delete','20','--yes']), 2)
            dispatch.assert_not_called()


class CommandTest(unittest.TestCase):
    def test_version_is_public_and_matches_capabilities(self):
        from bluebird_cli import __version__
        with patch.dict('os.environ', {'BLUEBIRD_CODE':'invalid'}), patch('bluebird_cli.cli.Store') as store, contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(SystemExit) as exit:
                cli.main(['--version'])
        self.assertEqual(exit.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), 'bluebird '+__version__)
        store.assert_not_called()
        result=Application().execute(cli.parser().parse_args(['capabilities']))
        self.assertEqual(result['cli_version'],__version__)
        self.assertEqual(result['version'],2)

    def test_helper_errors_show_runnable_owner_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            helper=Path(directory)/'bluebird-ax'
            with patch('bluebird_cli.macos.helper_path',return_value=helper):
                with self.assertRaisesRegex(RuntimeError,'bluebird --full-access setup'):
                    Bridge().call('doctor')
                helper.touch()
                with self.assertRaisesRegex(RuntimeError,'bluebird --full-access setup'):
                    Bridge().call('doctor')

    def test_invalid_commands_are_json(self):
        for args in ([], ['update','1'], ['add',' '], ['delete','not-an-id'], ['add','x','--duration','0']):
            with self.subTest(args=args):
                out = io.StringIO()
                with contextlib.redirect_stdout(out): self.assertEqual(cli.main(['--full-access', *args]), 2)
                self.assertFalse(json.loads(out.getvalue())['ok'])

    def test_start_web_port_boundaries_and_invalid_syntax(self):
        for value in ('0','1','65535'):
            with self.subTest(port=value):
                self.assertEqual(cli.parser().parse_args(['start','web','--port',value]).port,int(value))
        for argv in (['start'], ['start','unknown'], ['start','web','extra'], ['start','web','--host','0.0.0.0'],
                     ['web'], ['start','web','--port'], *[['start','web','--port',value] for value in ('-1','65536','1.5','abc','')]):
            with self.subTest(argv=argv), patch('bluebird_cli.web.serve') as serve, contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli.main(argv),2)
                self.assertEqual(json.loads(out.getvalue())['error']['code'],'invalid_argument')
                serve.assert_not_called()

    def test_start_web_bind_failure_is_json_not_success(self):
        with patch.dict('os.environ', {'BLUEBIRD_CODE':''}), patch('bluebird_cli.web.serve', side_effect=OSError('Address already in use')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(['start','web']),1)
        result=json.loads(out.getvalue())
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'],'operation_failed')

    def test_creation_returns_new_id_not_same_title(self):
        existing = {'id': '1', 'title': 'same'}
        new = {'id': '2', 'title': 'same'}
        with patch.object(cli.Store,'tasks',side_effect=[[existing],[existing,new]]), patch.object(Bridge,'open'):
            result = Application().add(cli.parser().parse_args(['add','same']))
        self.assertEqual(result, new)

    def test_locale_mismatch_prevents_ui_mutation(self):
        bridge = Mock()
        bridge.resources.return_value = {'localizations': {'en': {}, 'ja': {'Title': '日本語'}},
                                         'preferred_localizations': ['en']}
        bridge.snapshot.return_value = [{'role': 'AXTextField', 'description': '日本語'}]
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'BLUEBIRD_CLI_HOME': directory}):
            with self.assertRaisesRegex(RuntimeError, 'LOCALE_MISMATCH'):
                Application(bridge=bridge, locale='en', full_access=True).execute(cli.parser().parse_args(['complete', '1']))
        bridge.call.assert_not_called()
        bridge.open.assert_not_called()

    def test_unknown_outcome_not_success(self):
        with self.assertRaisesRegex(RuntimeError, 'UNVERIFIED'):
            wait_for(lambda: [], bool, 'creation', timeout=0)

    def test_mutations_are_serial(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'BLUEBIRD_CLI_HOME': directory}), mutation_lock(), self.assertRaisesRegex(RuntimeError, 'Another'):
            with mutation_lock(): pass


if __name__ == '__main__': unittest.main()
