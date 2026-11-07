import http.client
import json
import socket
import sqlite3
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

from bluebird_cli.auth import AccessDenied, Authority, PERMISSIONS
from bluebird_cli.web import make_server
from test_auth import FakeStore


class WebTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.authority = Authority(Path(self.tmp.name) / 'auth.sqlite3')
        self.store = FakeStore()
        self.server, self.url = make_server(self.authority, self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.token = parse_qs(urlsplit(self.url).fragment)['token'][0]
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()

    def request(self, path, method='GET', data=None, headers=None, raw=None, end_request=False):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        values = {'Authorization': 'Bearer ' + self.token, 'Origin': self.origin}
        if data is not None or raw is not None: values['Content-Type'] = 'application/json'
        values.update(headers or {})
        body=raw if raw is not None else json.dumps(data) if data is not None else None
        try:
            conn.request(method, path, body=body, headers=values)
            if end_request:conn.sock.shutdown(socket.SHUT_WR)
            response=conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_admin_lifecycle_and_agent_code_is_not_admin(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        status,_,body = self.request('/api/codes','POST',{'label':'Agent','tag_ids':['101'],'permissions':['list','get']})
        self.assertEqual(status,201)
        created = json.loads(body)['data']
        self.assertEqual(created['permissions'], ['get','list'])
        self.assertTrue(self.authority.resolve(created['code']).allows(self.store.items[0]))
        status,_,body = self.request('/api/state')
        self.assertEqual(status,200)
        self.assertNotIn(created['code'].encode(),body)
        self.assertEqual(self.request('/api/state',headers={'Authorization':'Bearer '+created['code']})[0],401)
        status,_,updated = self.request('/api/codes/'+created['id'],'PATCH',{'label':'Study','tag_ids':['102'],'permissions':['list']})
        self.assertEqual(status,200)
        self.assertNotIn('code',json.loads(updated)['data'])
        self.assertNotIn(created['code'].encode(),updated)
        self.assertEqual(self.request('/api/codes/'+created['id'])[0],404)
        self.assertEqual(self.authority.resolve(created['code']).permissions, frozenset(['list']))
        self.assertFalse(self.authority.resolve(created['code']).allows(self.store.items[0]))
        self.assertEqual(self.request('/api/codes/'+created['id']+'/revoke','POST',{})[0],200)
        with self.assertRaises(AccessDenied):self.authority.resolve(created['code'])

    def test_rejects_missing_auth_cross_origin_bad_host_and_empty_scope(self):
        self.assertEqual(self.request('/api/state',headers={'Authorization':''})[0],401)
        self.assertEqual(self.request('/api/state',headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/api/state',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('/api/codes','POST',{'label':'Agent','tag_ids':[]})[0],400)
        self.assertEqual(self.request('/api/codes','POST',{'label':'Agent','tag_ids':['101'],'permissions':['list','get']},headers={'Content-Type':'text/plain'})[0],415)
        for permissions in ([], ['web'], ['delete','unknown']):
            self.assertEqual(self.request('/api/codes','POST',{'label':'Agent','tag_ids':['101'],'permissions':permissions})[0],400)
        self.assertEqual(self.authority.list(),[])

    def test_json_body_types_and_malformed_encoding_never_create_grants(self):
        bodies=[b'', b'{', b'null', b'[]', b'true', b'42', b'"text"', b'\xff', b'{} trailing']
        for body in bodies:
            with self.subTest(body=body):
                status,_,response=self.request('/api/codes','POST',raw=body)
                self.assertEqual(status,400)
                self.assertFalse(json.loads(response)['ok'])
        self.assertEqual(self.authority.list(),[])
        self.assertEqual(self.request('/api/state')[0],200)

    def test_deeply_nested_json_is_a_client_error_and_server_survives(self):
        with patch.object(self.server, 'handle_error') as uncaught:
            status,_,body=self.request('/api/codes','POST',raw=b'['*2000+b']'*2000)
        self.assertEqual(status,400)
        self.assertFalse(json.loads(body)['ok'])
        uncaught.assert_not_called()
        self.assertEqual(self.authority.list(),[])
        self.assertEqual(self.request('/api/state')[0],200)

    def test_body_size_and_content_length_boundaries(self):
        payload={'label':'Boundary','tag_ids':['101'],'permissions':['list']}
        encoded=json.dumps(payload).encode()
        maximum=encoded+b' '*(65536-len(encoded))
        self.assertEqual(self.request('/api/codes','POST',raw=maximum)[0],201)
        before=self.authority.list()
        cases=[(maximum+b' ',{}), (b'',{'Content-Length':'0'}),
               (b'{}',{'Content-Length':'-1'}), (b'{}',{'Content-Length':'abc'}),
               (encoded,{'Content-Length':'+'+str(len(encoded))}),
               (b'{}',{'Content-Length':'65537'}), (b'{}',{'Transfer-Encoding':'chunked'})]
        for body,headers in cases:
            with self.subTest(headers=headers,size=len(body)):
                status,_,response=self.request('/api/codes','POST',raw=body,headers=headers)
                self.assertEqual(status,415 if 'Transfer-Encoding' in headers else 400)
                self.assertFalse(json.loads(response)['ok'])
                self.assertEqual(self.authority.list(),before)

    def test_incomplete_body_cannot_create_even_if_received_json_is_valid(self):
        body=json.dumps({'label':'Incomplete','tag_ids':['101'],'permissions':['get']}).encode()
        status,_,response=self.request('/api/codes','POST',raw=body,
                                      headers={'Content-Length':str(len(body)+1)},end_request=True)
        self.assertEqual(status,400)
        self.assertFalse(json.loads(response)['ok'])
        self.assertEqual(self.authority.list(),[])

    def test_missing_or_duplicate_length_headers_cannot_mutate(self):
        body=json.dumps({'label':'Bad length','tag_ids':['101'],'permissions':['get']}).encode()
        length=str(len(body))
        for lengths in ([], [length,length], [length,str(len(body)+1)]):
            with self.subTest(lengths=lengths):
                conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
                try:
                    conn.putrequest('POST','/api/codes')
                    conn.putheader('Authorization','Bearer '+self.token)
                    conn.putheader('Content-Type','application/json')
                    for value in lengths:conn.putheader('Content-Length',value)
                    conn.endheaders(body)
                    response=conn.getresponse()
                    self.assertEqual(response.status,400)
                    self.assertFalse(json.loads(response.read())['ok'])
                finally:conn.close()
                self.assertEqual(self.authority.list(),[])

    def test_request_body_timeout_does_not_write_or_report_storage_failure(self):
        body=json.dumps({'label':'Timeout','tag_ids':['101'],'permissions':['get']}).encode()
        status,_,response=self.request('/api/codes','POST',raw=body,
                                      headers={'Content-Length':str(len(body)+1)})
        self.assertEqual(status,408)
        self.assertFalse(json.loads(response)['ok'])
        self.assertEqual(self.authority.list(),[])
        self.assertEqual(self.request('/api/state')[0],200)

    def test_origin_credentials_and_server_sessions_cannot_be_substituted(self):
        for headers,status in (
            ({'Authorization':'Bearer wrong'},401), ({'Authorization':'Bearer é'},401),
            ({'Authorization':'bearer '+self.token},401),
            ({'Origin':'null'},403), ({'Origin':'http://localhost:'+str(self.server.server_port)},403),
            ({'Origin':self.origin+'.evil.example'},403), ({'Host':'localhost:'+str(self.server.server_port)},403),
        ):
            with self.subTest(headers=headers):self.assertEqual(self.request('/api/state',headers=headers)[0],status)
        second,url=make_server(self.authority,self.store)
        try:
            other_token=parse_qs(urlsplit(url).fragment)['token'][0]
            self.assertNotEqual(self.token,other_token)
            self.assertEqual(self.request('/api/state',headers={'Authorization':'Bearer '+other_token})[0],401)
        finally:second.server_close()
        self.assertEqual(self.request('/api/state')[0],200)

    def test_unknown_routes_and_wrong_methods_do_not_mutate(self):
        payload={'label':'Agent','tag_ids':['101'],'permissions':['get']}
        created=json.loads(self.request('/api/codes','POST',payload)[2])['data']
        before=self.authority.list()
        base='/api/codes/'+created['id']
        for path,method,status in ((base,'POST',404),(base+'/revoke','PATCH',404),
                                   ('/api/state','POST',404),('/api/codes','PATCH',404),
                                   ('/api/codes/not-an-id','PATCH',404),('/api/codes/'+'0'*24,'PATCH',400),
                                   ('/api/codes/'+'0'*24+'/revoke','POST',400)):
            with self.subTest(path=path,method=method):
                self.assertEqual(self.request(path,method,payload)[0],status)
                self.assertEqual(self.authority.list(),before)
        self.assertEqual(self.request(base,'DELETE')[0],501)
        self.assertEqual(self.authority.list(),before)

    def test_revocation_is_idempotent_and_update_cannot_restore_code(self):
        payload={'label':'Agent','tag_ids':['101'],'permissions':['get']}
        created=json.loads(self.request('/api/codes','POST',payload)[2])['data']
        path='/api/codes/'+created['id']
        status,_,first=self.request(path+'/revoke','POST',{})
        self.assertEqual(status,200)
        status,_,second=self.request(path+'/revoke','POST',{})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(first),json.loads(second))
        self.assertNotIn(created['code'].encode(),first)
        self.assertNotIn('digest',json.loads(first)['data'])
        self.assertEqual(self.request(path,'PATCH',payload)[0],400)
        with self.assertRaises(AccessDenied):self.authority.resolve(created['code'])

    def test_storage_failures_are_json_and_hide_private_details(self):
        for target,method,error in ((self.store,'tags',OSError('private/path/secret')),
                                    (self.authority,'list',sqlite3.OperationalError('private/path/secret'))):
            with self.subTest(method=method), patch.object(target,method,side_effect=error):
                status,_,body=self.request('/api/state')
                self.assertEqual(status,503)
                self.assertFalse(json.loads(body)['ok'])
                self.assertNotIn(b'private/path/secret',body)
        with patch.object(self.authority,'create',side_effect=sqlite3.OperationalError('locked')):
            self.assertEqual(self.request('/api/codes','POST',{'label':'Agent','tag_ids':['101'],'permissions':['get']})[0],503)
        self.assertEqual(self.authority.list(),[])
        self.assertEqual(self.request('/api/state')[0],200)

    def test_port_collision_fails_without_replacing_running_console(self):
        with self.assertRaises(OSError):make_server(self.authority,self.store,self.server.server_port)
        self.assertEqual(self.request('/api/state')[0],200)

    def test_static_assets_have_no_secrets_and_cannot_read_arbitrary_paths(self):
        for path in ('/','/codes','/app.js','/style.css'):
            status,headers,body = self.request(path,headers={'Authorization':''})
            self.assertEqual(status,200)
            self.assertNotIn(self.token.encode(),body)
            self.assertEqual(headers['Cache-Control'],'no-store')
            self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(self.request('/../auth.sqlite3')[0],404)
        self.assertEqual(self.request('/api/codes','GET')[0],404)


if __name__ == '__main__': unittest.main()
