from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bluebird_cli.cli import parser
from bluebird_cli.domain import ensure_unique, expected_fields
from bluebird_cli.workflow import Workflow


class WorkflowTest(unittest.TestCase):
    def test_duplicate_titles_never_mutate(self):
        for other in ('same', 'same، metadata', 'same another'):
            store, ui = Mock(), Mock()
            task = {'id': '1', 'title': 'same', 'status': 'active'}
            store.get.return_value = task
            store.tasks.return_value = [task, {'id': '2', 'title': other, 'status': 'active'}]
            with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS'):
                Workflow(store, ui).task(SimpleNamespace(command='complete', id='1'))
            self.assertFalse(ui.mock_calls)

    def test_deleted_duplicate_does_not_block(self):
        task = {'title': 'same', 'status': 'active'}
        ensure_unique([task, {'title': 'same', 'status': 'deleted'}], task)

    def test_clear_fields_are_explicit(self):
        args = parser().parse_args(['update', '1', '--duration', '0', '--priority', 'none', '--tags', '', '--notes', ''])
        self.assertEqual(expected_fields(args), {'duration': 0, 'priority': 0, 'tags': [], 'notes': ''})

    def test_idempotent_completion_never_opens_app(self):
        store, ui = Mock(), Mock()
        store.get.return_value = {'id': '1', 'status': 'completed'}
        self.assertEqual(Workflow(store, ui).task(SimpleNamespace(command='complete', id='1')), store.get.return_value)
        self.assertFalse(ui.mock_calls)

    def test_update_verifies_persisted_fields(self):
        store, ui = Mock(), Mock()
        before = {'id': '1', 'title': 'task', 'notes': 'before', 'status': 'active'}
        after = dict(before, notes='after')
        store.get.side_effect = [before, after]
        store.tasks.return_value = [before]
        result = Workflow(store, ui).task(parser().parse_args(['update', '1', '--notes', 'after']))
        ui.edit_task.assert_called_once_with(before, {'notes': 'after'})
        self.assertEqual(result, after)

    def test_timer_normalizes_non_five_minute_offset(self):
        store, ui = Mock(), Mock()
        task = {'id': '1', 'title': 'test', 'status': 'active'}
        store.get.return_value = task
        store.tasks.return_value = [task]
        state = {'state': 'idle', 'task_id': '1', 'duration': 2, 'values': {'focus.sessionDuration': '120'}}
        store.timer.side_effect = lambda: state
        def adjust(action):
            seconds = max(0, float(state['values']['focus.sessionDuration']) + (300 if action == 'AXIncrement' else -300))
            state['values']['focus.sessionDuration'] = str(seconds)
            state['duration'] = seconds / 60
        ui.adjust_duration.side_effect = adjust
        ui.start_timer.side_effect = lambda: state.update(state='focusing')
        result = Workflow(store, ui).timer(SimpleNamespace(action='start', task='1', duration=5))
        self.assertEqual([call.args[0] for call in ui.adjust_duration.call_args_list], ['AXDecrement', 'AXIncrement'])
        self.assertEqual((result['duration'], result['state']), (5, 'focusing'))

    def test_timer_does_not_replace_existing_session(self):
        store, ui = Mock(), Mock()
        store.timer.return_value = {'state': 'focusing'}
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            Workflow(store, ui).timer(SimpleNamespace(action='start'))
        self.assertFalse(ui.mock_calls)

    def test_wrong_selected_task_never_starts(self):
        store, ui = Mock(), Mock()
        task = {'id': '1', 'title': 'test', 'status': 'active'}
        store.get.return_value = task
        store.tasks.return_value = [task]
        store.timer.return_value = {'state': 'idle', 'task_id': '2'}
        with self.assertRaisesRegex(RuntimeError, 'does not match'):
            Workflow(store, ui).timer(SimpleNamespace(action='start', task='1', duration=None))
        ui.start_timer.assert_not_called()

    def test_timer_rejects_unsupported_duration_before_ui(self):
        with self.assertRaises(ValueError):
            parser().parse_args(['timer', 'start', '--task', '1', '--duration', '1'])


if __name__ == '__main__': unittest.main()
