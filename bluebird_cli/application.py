"""Application entry points and backend composition, independent of argument parsing."""
from pathlib import Path
import sqlite3
import sys

from . import __version__
from .auth import Access, AccessDenied, Authority, PUBLIC_COMMANDS, ADMIN_COMMANDS, PERMISSION_GROUPS, PERMISSIONS
from .domain import expected_fields, matches
from .localization import Catalog
from .macos import Bridge, helper_path, setup
from .runtime import mutation_lock, wait_for
from .store import Store, DEFAULT_DB
from .ui import BluebirdUI
from .url_scheme import build_url
from .workflow import Workflow


class Application:
    def __init__(self, store=None, bridge=None, locale='auto', full_access=False, code=None, authority=None):
        self.store = store if store is not None else Store()
        self.bridge = bridge if bridge is not None else Bridge()
        self.locale = locale
        self.full_access = full_access
        self.code = code
        self.authority = authority if authority is not None else Authority()

    def access(self):
        if self.full_access and self.code is not None:
            raise AccessDenied('Choose full-access or a code, not both')
        if self.full_access:
            return Access()
        if self.code is not None:
            return self.authority.resolve(self.code)
        raise AccessDenied('Choose --full-access or --code CODE (or set BLUEBIRD_CODE)')

    def scoped_task(self, access, task_id):
        try:
            task = self.store.get(task_id)
        except ValueError:
            if access.full:
                raise
            raise AccessDenied('Task unavailable in this code scope') from None
        return access.require_task(task)

    def authorize_write(self, access, args):
        if access.full:
            return
        if self.store.path != DEFAULT_DB.resolve():
            raise AccessDenied('Code mode requires the default live Bluebird store')
        if hasattr(args, 'id'):
            self.scoped_task(access, args.id)
        if args.command == 'add' or args.command == 'update' and args.tags is not None:
            access.validate_tags(args.tags, self.store)
        if args.command == 'timer':
            if args.action == 'start':
                self.scoped_task(access, args.task)
            else:
                current = self.store.timer()
                if current.get('task_id') is None:
                    raise AccessDenied('Current timer is unavailable in this code scope')
                self.scoped_task(access, current['task_id'])

    def catalog(self):
        return Catalog(self.bridge.resources(), self.locale)

    def doctor(self):
        checks = {'macos': sys.platform == 'darwin', 'database': str(self.store.path),
                  'helper': helper_path().is_file()}
        try:
            checks['task_count'] = len(self.store.tasks('all'))
        except (OSError, sqlite3.Error, RuntimeError) as error:
            checks['database_error'] = str(error)
        if checks['helper']:
            try:
                checks.update(self.bridge.call('doctor'))
                catalog = self.catalog()
                checks['app_version'] = catalog.metadata.get('version')
                checks['available_locales'] = sorted(catalog.tables)
                if checks.get('trusted'):
                    checks['locale'] = catalog.detect(self.bridge.snapshot())
            except (OSError, RuntimeError, ValueError) as error:
                checks['adapter_error'] = str(error)
        checks['ready'] = (checks['macos'] and checks.get('trusted', False)
                           and 'database_error' not in checks and 'adapter_error' not in checks)
        return checks

    def execute(self, args):
        cmd = f'start {args.service}' if args.command == 'start' else args.command
        if cmd == 'start web':
            if self.code is not None:
                raise AccessDenied('start web is an owner command; omit --code and unset BLUEBIRD_CODE')
            if self.store.path != DEFAULT_DB.resolve():
                raise ValueError('Web management requires the default live Bluebird store')
            from .web import serve
            return serve(self.authority, self.store, args.port)
        access = self.access() if cmd not in PUBLIC_COMMANDS else None
        if access is not None and not access.full:
            if cmd in ADMIN_COMMANDS:
                raise AccessDenied(f'{cmd} requires --full-access')
            access.require_command(args)
            if self.store.path != DEFAULT_DB.resolve():
                raise AccessDenied('Code mode requires the default live Bluebird store')
        if cmd == 'auth-status':
            return {'mode': 'full-access' if access.full else 'code', 'grant_id': access.grant_id,
                    'tag_ids': sorted(access.tag_ids), 'permissions': sorted(PERMISSIONS if access.full else access.permissions),
                    'tags': [tag for tag in self.store.tags() if access.full or tag['id'] in access.tag_ids],
                    'rule': 'nonempty_all_tags'}
        if cmd == 'tags':
            return [tag for tag in self.store.tags() if access.full or tag['id'] in access.tag_ids]
        if cmd == 'setup':
            return setup()
        if cmd == 'doctor':
            return self.doctor()
        if cmd == 'locales':
            return self.catalog().report()
        if cmd == 'capabilities':
            return {'version': 2, 'cli_version': __version__,
                    'access': {'modes': ['--full-access', '--code CODE', 'BLUEBIRD_CODE'],
                               'public_commands': sorted(PUBLIC_COMMANDS), 'admin_commands': sorted(ADMIN_COMMANDS),
                               'owner_entrypoints': ['start web'],
                               'code_scope': 'nonempty_all_task_tag_ids_subset_of_grant',
                               'permission_groups': PERMISSION_GROUPS,
                               'exit_code_denied': 3},
                    'commands': ['open', 'focus', 'add', 'list', 'get', 'update', 'complete', 'reopen', 'delete',
                                 'timer status', 'timer start', 'timer stop', 'timer finish', 'timer reset',
                                 'logs', 'ui', 'doctor', 'setup', 'locales', 'tags', 'auth-status', 'start web'],
                    'task_fields': ['title', 'notes', 'duration', 'priority', 'tags'],
                    'duration_unit': 'minutes', 'timer_duration_step': 5, 'id_type': 'string',
                    'ui_languages': {'source': 'installed_app_bundle', 'discovery': 'locales',
                                     'selection': '--locale auto|LOCALE'},
                    'backend': {'read': 'sqlite_readonly', 'create': 'url_scheme', 'mutate': 'macos_accessibility'},
                    'output': {'ok': 'boolean', 'data': 'result on success', 'error': 'code/message on failure'},
                    'requires': ['macOS', 'compatible Bluebird schema/UI', 'Python 3.9+',
                                 'Swift compiler for setup', 'Accessibility permission for UI mutations'],
                    'limitations': ['UI automation requires an unlocked logged-in desktop',
                                    'Language resource coverage is not per-language live certification',
                                    'No guarantee of iCloud/iPhone/Watch sync or notifications',
                                    'Date/recurrence editing is not exposed by this CLI']}
        if cmd == 'list':
            return [task for task in self.store.tasks(args.status, args.search) if access.allows(task)]
        if cmd == 'get':
            return self.scoped_task(access, args.id)
        if cmd == 'logs':
            if access.full:
                return self.store.logs(args.task)
            if args.task is not None:
                self.scoped_task(access, args.task)
            permitted = {task['id'] for task in self.store.tasks('all') if access.allows(task)}
            return [log for log in self.store.logs(args.task) if log['task_id'] in permitted]
        if cmd == 'ui':
            catalog = self.catalog()
            nodes = self.bridge.snapshot()
            return {'locale': catalog.detect(nodes), 'nodes': nodes}
        if cmd == 'timer' and args.action == 'status':
            return access.timer_view(self.store.timer(), self.store)
        if cmd in ('open', 'focus'):
            url = build_url(args)
            if not args.dry_run:
                self.bridge.open(url)
            return {'url': url, 'status': 'preview' if args.dry_run else 'dispatched'}
        if cmd == 'update' and not expected_fields(args):
            raise ValueError('update requires at least one field')
        if cmd == 'delete' and not args.yes and not args.dry_run:
            raise ValueError('delete requires --yes and an exact task ID')
        self.authorize_write(access, args)
        if getattr(args, 'dry_run', False):
            plan = {key: str(value) if isinstance(value, Path) else value
                    for key, value in vars(args).items() if value is not None and key not in ('code', 'full_access')}
            if hasattr(args, 'id'):
                plan['task'] = self.scoped_task(access, args.id)
            if cmd == 'timer' and args.action == 'start':
                plan['task'] = self.scoped_task(access, args.task)
            if cmd == 'add':
                plan['url'] = build_url(args)
            return {'status': 'preview', 'plan': plan}
        if self.store.path != DEFAULT_DB.resolve():
            raise ValueError('Mutations require the default live Bluebird store; --db is read-only')
        with mutation_lock():
            access = self.access()
            access.require_command(args)
            self.authorize_write(access, args)
            if cmd == 'add':
                return access.require_task(self.add(args))
            # Readiness is checked before any UI write, including language mismatches.
            adapter = BluebirdUI(self.bridge, self.catalog())
            adapter.snapshot()
            workflow = Workflow(self.store, adapter, authorize=None if access.full else access.require_task)
            result = workflow.timer(args) if cmd == 'timer' else workflow.task(args)
            return access.timer_view(result, self.store) if cmd == 'timer' else access.require_task(result)

    def add(self, args):
        before = {task['id'] for task in self.store.tasks('all')}
        self.bridge.open(build_url(args))
        expected = expected_fields(args)

        def created():
            return [task for task in self.store.tasks('all') if task['id'] not in before and task['title'] == args.title]

        found = wait_for(created, lambda tasks: len(tasks) > 1 or (len(tasks) == 1 and matches(tasks[0], expected)),
                         'task creation')
        if len(found) != 1:
            raise RuntimeError('AMBIGUOUS: multiple new tasks matched. Inspect list before retrying.')
        return found[0]
