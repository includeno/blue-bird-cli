import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from bluebird_cli.cli import parser
from bluebird_cli.macos import Bridge
from bluebird_cli.url_scheme import build_url


class URLTests(unittest.TestCase):
    def test_unicode_and_reserved_characters(self):
        title = '写代码 & review? #1 + 50% / "测试" $(echo no)'
        args = parser().parse_args(['add', title, '--notes', '第一行\n第二行&priority=1',
                                   '--duration', '25', '--priority', 'high', '--tags', '工作,学习'])
        self.assertEqual(parse_qs(urlsplit(build_url(args)).query),
                         {'title': [title], 'notes': ['第一行\n第二行&priority=1'], 'duration': ['25'],
                          'priority': ['3'], 'tags': ['工作,学习']})

    def test_optional_fields_and_routes(self):
        self.assertEqual(build_url(parser().parse_args(['add', 'Task'])), 'bluebird://add?title=Task')
        self.assertEqual(build_url(parser().parse_args(['open'])), 'bluebird:')
        self.assertEqual(build_url(parser().parse_args(['focus'])), 'bluebird://focus')
        for label, number in (('low', '1'), ('medium', '2'), ('high', '3')):
            self.assertIn('priority=' + number, build_url(parser().parse_args(['add','Task','--priority',label])))

    def test_dispatch_uses_argv_and_reports_errors(self):
        with patch('bluebird_cli.macos.sys.platform', 'darwin'), patch('bluebird_cli.macos.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([],0,'','')
            Bridge().open('bluebird:')
            self.assertEqual(run.call_args.args[0], ['/usr/bin/open','-b','com.cub-and-pup.Bluebird','bluebird:'])
            run.return_value = subprocess.CompletedProcess([],1,'','App missing')
            with self.assertRaisesRegex(RuntimeError, 'App missing'): Bridge().open('bluebird:')
