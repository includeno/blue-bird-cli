"""Exercise the real service entry point without opening or mutating Bluebird."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import unittest
from urllib.parse import urlsplit
from urllib.request import urlopen


class WebCLITest(unittest.TestCase):
    def test_start_web_prints_private_url_serves_page_and_shuts_down(self):
        environment=dict(os.environ)
        environment.pop('BLUEBIRD_CODE', None)
        launcher=Path(__file__).resolve().parents[1] / 'bluebird'
        process=subprocess.Popen([sys.executable,str(launcher),'start','web','--port','0'],
                                 env=environment,stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertTrue(select.select([process.stdout],[],[],10)[0], 'Server did not report startup')
            started=json.loads(process.stdout.readline())
            self.assertTrue(started['ok'])
            self.assertEqual(started['data']['mode'],'full-access')
            url=urlsplit(started['data']['url'])
            self.assertEqual(url.hostname,'127.0.0.1')
            self.assertGreater(url.port,0)
            self.assertTrue(url.fragment.startswith('token='))
            with urlopen(url._replace(fragment='').geturl(),timeout=5) as response:
                html=response.read().decode()
                self.assertEqual(response.status,200)
                self.assertIn('bluebird start web',html)
                self.assertNotIn(url.fragment.removeprefix('token='),html)
            process.send_signal(signal.SIGINT)
            stdout,stderr=process.communicate(timeout=5)
            self.assertEqual(process.returncode,0,stderr)
            self.assertEqual(json.loads(stdout),{'ok':True,'data':{'status':'stopped'}})
            self.assertEqual(stderr,'')
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()


if __name__ == '__main__': unittest.main()
