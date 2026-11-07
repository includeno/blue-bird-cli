"""Loopback-only owner UI. Agent codes never authenticate to this admin API."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import secrets
import socket
from socketserver import TCPServer
import sqlite3

from .auth import PERMISSION_GROUPS

ASSETS = Path(__file__).parent / 'web_assets'


class LoopbackServer(ThreadingHTTPServer):
    def server_bind(self):
        # A numeric loopback address needs no potentially blocking reverse DNS lookup.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address


def make_server(authority, store, port=0):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data, content_type='application/json; charset=utf-8'):
            body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def error(self, status, message):
            self.reply(status, {'ok': False, 'error': {'message': message}})

        def handle_request(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != origin.removeprefix('http://') or self.headers.get('Origin', origin) != origin:
                return self.error(403, 'This console only accepts its own loopback origin')
            if self.command == 'GET' and self.path == '/favicon.ico':
                return self.reply(204, b'', 'image/x-icon')
            assets = {'/codes': ('index.html', 'text/html; charset=utf-8'), '/': ('index.html', 'text/html; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if self.command == 'GET' and self.path in assets:
                name, mime = assets[self.path]
                return self.reply(200, (ASSETS / name).read_bytes(), mime)
            if not self.path.startswith('/api/'):
                return self.error(404, 'Not found')
            credential = self.headers.get('Authorization', '')
            if not secrets.compare_digest(credential.encode(), ('Bearer ' + token).encode()):
                return self.error(401, 'Open the console using the private URL printed by bluebird start web')
            try:
                if self.command == 'GET' and self.path == '/api/state':
                    return self.reply(200, {'ok': True, 'data': {'tags': store.tags(), 'codes': authority.list(), 'permission_groups': PERMISSION_GROUPS}})
                match = re.fullmatch(r'/api/codes/([a-f0-9]{24})(/revoke)?', self.path)
                if self.command not in ('POST', 'PATCH'):
                    return self.error(404, 'Not found')
                if self.headers.get_content_type() != 'application/json' or self.headers.get('Transfer-Encoding'):
                    return self.error(415, 'Use application/json with Content-Length')
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or not lengths[0].strip().isascii() or not lengths[0].strip().isdecimal():
                    return self.error(400, 'Expected one valid Content-Length header')
                size = int(lengths[0])
                if not 0 < size <= 65536:
                    return self.error(400, 'Invalid request size')
                self.connection.settimeout(5)
                try:
                    body = self.rfile.read(size)
                except socket.timeout:
                    return self.error(408, 'Request body timed out')
                if len(body) != size:
                    return self.error(400, 'Incomplete request body')
                try:
                    payload = json.loads(body)
                except RecursionError:
                    return self.error(400, 'JSON nesting is too deep')
                if not isinstance(payload, dict):
                    raise ValueError('Expected a JSON object')
                if self.command == 'POST' and self.path == '/api/codes':
                    result = authority.create(payload.get('label'), payload.get('tag_ids'), payload.get('permissions'), store.tags())
                    return self.reply(201, {'ok': True, 'data': result})
                if match and self.command == 'PATCH' and not match[2]:
                    result = authority.update(match[1], payload.get('label'), payload.get('tag_ids'), payload.get('permissions'), store.tags())
                elif match and self.command == 'POST' and match[2]:
                    result = authority.revoke(match[1])
                else:
                    return self.error(404, 'Not found')
                return self.reply(200, {'ok': True, 'data': result})
            except (ValueError, UnicodeError) as error:
                self.error(400, str(error))
            except (OSError, sqlite3.Error, RuntimeError):
                self.error(503, 'Local storage unavailable. Check bluebird --full-access doctor in the terminal.')

        do_GET = handle_request
        do_POST = handle_request
        do_PATCH = handle_request

    server = LoopbackServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server, f'http://127.0.0.1:{server.server_port}/#token={token}'


def serve(authority, store, port):
    server, url = make_server(authority, store, port)
    print(json.dumps({'ok': True, 'data': {'url': url, 'mode': 'full-access',
                                         'message': 'Private local admin URL. Keep this process running; Ctrl+C stops it.'}}), flush=True)
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return {'status': 'stopped'}
