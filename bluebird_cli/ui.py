"""Semantic Bluebird UI adapter. Workflows never depend on translated labels."""
import time

from .domain import display_text, label_prefix

# Stable IDs are preferred; resource keys are the fallback for unlabelled identifiers.
CONTROLS = {
    'title': (('AXTextField',), (), ('title',)),
    'notes': (('AXTextArea',), (), ('notes',)),
    'duration': (('AXButton',), (), ('task_duration',)),
    'priority': (('AXSlider',), (), ('priority',)),
    'tags': (('AXButton',), (), ('tags',)),
    'new_tag': (('AXButton',), ('plus',), ('new_tag',)),
    'tag_name': (('AXTextField',), (), ('tag_name',)),
    'save': (('AXButton',), (), ('save',)),
    'clear': (('AXButton',), (), ('clear',)),
    'done': (('AXButton',), (), ('done',)),
    'back': (('AXButton', 'AXGenericElement'), ('BackButton',), ('back',)),
    'hours': (('AXTextField',), (), ('hour', 'hours')),
    'minutes': (('AXTextField',), (), ('minute', 'minutes')),
    'today': (('AXMenuItem',), (), ('today',)),
    'completed': (('AXMenuItem',), (), ('completed',)),
    'scheduled': (('AXMenuItem',), (), ('scheduled',)),
    'delete': (('AXButton',), (), ('delete',)),
    'session_duration': (('AXSlider',), (), ('session_duration',)),
    'timer_start': (('AXButton',), ('play.circle',), ('start',)),
    'timer_finish': (('AXButton',), ('checkmark',), ('finish',)),
    'timer_stop': (('AXButton',), ('stop.circle',), ('stop',)),
    'timer_reset': (('AXButton',), ('arrowshape.turn.up.backward',), ('back',)),
    'timer_close': (('AXButton',), ('xmark', 'rectangle.portrait.and.arrow.forward'), ()),
    'discard_progress': (('AXButton',), (), ('discard_progress',)),
}


def selector(node):
    result = {'role': node['role']}
    if 'path' in node:
        result['path'] = node['path']
    # Revalidate identity at the snapshot path, never silently select another equal label.
    for key in ('identifier', 'description', 'title', 'placeholder'):
        if node.get(key):
            result[key] = node[key]
    return result


def text_matches(node, labels, prefix=False):
    compare = label_prefix if prefix else lambda a, b: display_text(a) == display_text(b)
    return any(compare(node.get(field, ''), label) for field in ('description', 'title', 'placeholder')
               for label in labels)


class BluebirdUI:
    def __init__(self, bridge, catalog):
        self.bridge = bridge
        self.catalog = catalog

    def snapshot(self):
        nodes = self.bridge.snapshot()
        self.catalog.detect(nodes)
        return nodes

    def choose(self, control, nodes):
        roles, identifiers, semantics = CONTROLS[control]
        candidates = [node for node in nodes if node['role'] in roles]
        by_id = [node for node in candidates if node.get('identifier') in identifiers]
        if control == 'back' and not by_id:
            # UIKit's back label may differ from the app's Back translation (e.g. French).
            add_buttons = [node for node in nodes if node.get('identifier') == 'plus' and node['role'] == 'AXButton'
                           and any(parent['role'] == 'AXPopover' and node.get('path', [])[:len(parent.get('path', []))] == parent.get('path')
                                   for parent in nodes)]
            if add_buttons:
                if len(add_buttons) != 1:
                    raise RuntimeError('AMBIGUOUS: multiple tag navigation bars')
                parent_path = add_buttons[0]['path'][:-1]
                found = [node for node in candidates if node.get('path', [])[:-1] == parent_path
                         and node.get('identifier') != 'plus']
                if len(found) != 1:
                    raise RuntimeError('Tag navigation structure changed; cannot identify Back')
                return found[0]
        found = by_id or [node for node in candidates if text_matches(
            node, self.catalog.labels(*semantics), prefix=control == 'tags')]
        if len(found) > 1:
            raise RuntimeError(f'AMBIGUOUS: multiple controls for {control}; no action taken')
        return found[0] if found else None

    def find(self, control, timeout=3):
        deadline = time.monotonic() + timeout
        while True:
            node = self.choose(control, self.snapshot())
            if node is not None:
                return node
            if time.monotonic() >= deadline:
                raise RuntimeError(f'Control unavailable: {control}; inspect bluebird ui')
            time.sleep(0.15)

    def call_on(self, node, operation, **kwargs):
        identity = {key: value for key, value in selector(node).items() if key != 'path'}
        for attempt in range(3):
            try:
                return self.bridge.call(operation, selector=selector(node), **kwargs)
            except RuntimeError as error:
                # A zero-match error precedes the action; animations may move the tree path.
                if 'Expected one UI element, found 0;' not in str(error) or attempt == 2:
                    raise
                time.sleep(0.15)
                candidates = [item for item in self.snapshot()
                              if all(item.get(key) == value for key, value in identity.items())
                              and item.get('selected') == node.get('selected')]
                if len(candidates) != 1:
                    raise RuntimeError('UI target changed or became ambiguous; no retry performed') from error
                node = candidates[0]

    def action(self, node, action='AXPress'):
        return self.call_on(node, 'action', action=action)

    def press(self, control):
        return self.action(self.find(control))

    def custom(self, node, semantic):
        labels = {display_text(label) for label in self.catalog.labels(semantic)}
        actions = [action for action in node.get('actions', [])
                   if display_text(action['description']) in labels]
        if len(actions) != 1:
            raise RuntimeError(f'Task action unavailable or ambiguous: {semantic}')
        self.action(node, actions[0]['name'])

    def task_row(self, task, nodes):
        labels = set(self.catalog.labels('mark_complete', 'mark_incomplete'))
        found = [node for node in nodes if node['role'] in ('AXGenericElement', 'AXStaticText')
                 and label_prefix(node.get('description', ''), task['title'])
                 and any(display_text(action['description']) in {display_text(x) for x in labels}
                         for action in node.get('actions', []))]
        if len(found) > 1:
            raise RuntimeError('AMBIGUOUS: multiple task rows match the requested title')
        return found[0] if found else None

    def locate(self, task):
        self.bridge.open('bluebird:')
        self.bridge.call('activate')
        nodes = self.snapshot()
        if any(node['role'] in ('AXSheet', 'AXPopover') for node in nodes):
            raise RuntimeError('Bluebird has an open editor/dialog; save or cancel it first')
        if any(node.get('identifier') in ('play.circle', 'rectangle.portrait.and.arrow.forward') for node in nodes):
            self.press('timer_close')
            self.find('today')
            nodes = self.snapshot()
        row = self.task_row(task, nodes)
        if row:
            return row
        for section in (('completed',) if task['status'] == 'completed' else ('today', 'scheduled')):
            self.press(section)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                row = self.task_row(task, self.snapshot())
                if row:
                    return row
                time.sleep(0.15)
        raise RuntimeError('Task is not exposed in its list; scroll to it in Bluebird and retry')

    def set_field(self, control, value):
        node = self.find(control)
        operation = 'type' if control in ('notes', 'tag_name') else 'set'
        self.call_on(node, operation, value=str(value))
        time.sleep(0.2)

    def find_tag(self, name, timeout=3):
        deadline = time.monotonic() + timeout
        while True:
            nodes = [node for node in self.snapshot() if node['role'] == 'AXButton'
                     and text_matches(node, (name,))]
            if len(nodes) > 1:
                raise RuntimeError(f'AMBIGUOUS: tag name conflicts with another control: {name}')
            if nodes:
                return nodes[0]
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.15)

    def edit_tags(self, current, wanted):
        self.press('tags')
        self.find('new_tag')
        for name in wanted:
            if self.find_tag(name, timeout=0) is None:
                self.press('new_tag')
                self.set_field('tag_name', name)
                self.bridge.call('key', key=36)
                if self.find_tag(name) is None:
                    raise RuntimeError('UNVERIFIED: new tag was not exposed; inspect Bluebird before retrying')
        # Only touch task tag names, never every selected control in the dialog.
        for name in sorted(set(current) | set(wanted)):
            node = self.find_tag(name)
            if node is None or 'selected' not in node:
                raise RuntimeError(f'Tag selection state unavailable: {name}')
            if node['selected'] != (name in wanted):
                self.action(node)
        self.press('back')

    def edit_task(self, task, expected):
        self.action(self.locate(task))
        if self.find('title').get('value') != task['title']:
            raise RuntimeError('Editor does not match the requested task; no fields changed')
        for key in ('title', 'notes'):
            if key in expected:
                self.set_field(key, expected[key])
        if 'duration' in expected:
            self.press('duration')
            if expected['duration'] == 0:
                self.press('clear')
            else:
                self.set_field('hours', expected['duration'] // 60)
                self.set_field('minutes', expected['duration'] % 60)
                self.press('done')
        if 'priority' in expected:
            for _ in range(3):
                self.action(self.find('priority'), 'AXDecrement')
            for _ in range(expected['priority']):
                self.action(self.find('priority'), 'AXIncrement')
        if 'tags' in expected and sorted(task['tags']) != expected['tags']:
            self.edit_tags(task['tags'], expected['tags'])
        self.press('save')

    def change_status(self, task, command):
        semantic = {'complete': 'mark_complete', 'reopen': 'mark_incomplete', 'delete': 'delete'}[command]
        self.custom(self.locate(task), semantic)
        if command == 'delete':
            time.sleep(0.3)
            button = self.choose('delete', self.snapshot())
            if button is not None:
                self.action(button)

    def prepare_focus(self, task):
        self.custom(self.locate(task), 'focus')
        self.find('timer_start')

    def adjust_duration(self, action):
        self.action(self.find('session_duration'), action)

    def start_timer(self):
        self.press('timer_start')

    def end_timer(self, action):
        self.bridge.open('bluebird://focus')
        self.bridge.call('activate')
        self.press({'finish': 'timer_finish', 'stop': 'timer_stop', 'reset': 'timer_reset'}[action])
        if action == 'stop':
            self.press('discard_progress')
