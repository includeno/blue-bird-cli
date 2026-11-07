"""Task/timer use cases. Depends on semantic UI operations, never locale text."""
from .domain import ensure_unique, expected_fields, matches
from .runtime import wait_for


class Workflow:
    def __init__(self, store, ui, authorize=None):
        self.store = store
        self.ui = ui
        self.check_access = authorize is not None
        self.authorize = authorize or (lambda task: task)

    def task(self, args):
        task = self.authorize(self.store.get(args.id))
        desired = {'complete': 'completed', 'reopen': 'active', 'delete': 'deleted'}.get(args.command)
        if desired == task['status']:
            return task
        if task['status'] == 'deleted':
            raise ValueError('Cannot modify a deleted task')
        expected = expected_fields(args) if args.command == 'update' else {'status': desired}
        if matches(task, expected):
            return task
        ensure_unique(self.store.tasks('all'), task)
        if args.command == 'update':
            self.ui.edit_task(task, expected)
        else:
            self.ui.change_status(task, args.command)
        return wait_for(lambda: self.store.get(task['id']), lambda value: matches(value, expected),
                        f'{args.command} task {task["id"]}')

    def timer(self, args):
        current = self.store.timer()
        if args.action == 'start':
            if current['state'] != 'idle':
                raise RuntimeError('A focus/break session already exists; inspect timer status first')
            task = self.authorize(self.store.get(args.task))
            if task['status'] != 'active':
                raise ValueError('Focus requires an active task')
            ensure_unique(self.store.tasks('all'), task)
            self.ui.prepare_focus(task)
            if args.duration is not None:
                self.adjust_duration(args.duration)
            if self.store.timer()['task_id'] != task['id']:
                raise RuntimeError('Selected focus task does not match requested ID')
            self.ui.start_timer()
            return wait_for(self.store.timer, lambda state: state['state'] == 'focusing'
                            and state['task_id'] == task['id']
                            and (args.duration is None or state['duration'] == args.duration), 'start focus')
        if self.check_access and current.get('task_id') is not None:
            self.authorize(self.store.get(current['task_id']))
        if args.action == 'reset':
            if current['state'] == 'focusing':
                raise ValueError('Use timer finish to save progress or timer stop to discard it before reset')
            if current['state'] == 'idle':
                return current
        elif current['state'] != 'focusing':
            raise ValueError('No focus session is running')
        self.ui.end_timer(args.action)
        return wait_for(self.store.timer, lambda state: state['state'] != 'focusing'
                        if args.action == 'finish' else state['state'] == 'idle', f'{args.action} focus')

    def adjust_duration(self, minutes):
        target, seen = minutes * 60, set()
        for _ in range(240):
            before = float(self.store.timer()['values'].get('focus.sessionDuration') or 0)
            if before == target:
                return
            if before in seen:
                raise RuntimeError('Timer duration control did not converge; no session started')
            seen.add(before)
            action = 'AXIncrement' if before < target and before % 300 == 0 else 'AXDecrement'
            self.ui.adjust_duration(action)
            wait_for(self.store.timer, lambda state: float(state['values'].get('focus.sessionDuration') or 0) != before,
                     'adjust session duration', timeout=2)
        raise RuntimeError('Could not reach requested session duration; timer was not started')
