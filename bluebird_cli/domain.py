"""Task semantics shared by URL creation, UI updates and result verification."""
import unicodedata

PRIORITIES = {'none': 0, 'low': 1, 'medium': 2, 'high': 3}
BIDI_MARKS = dict.fromkeys(map(ord, '\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'))


def display_text(value):
    """Compare display labels without changing stored user text or emoji joins."""
    return ' '.join(unicodedata.normalize('NFC', value).translate(BIDI_MARKS).split())


def label_prefix(label, prefix):
    label, prefix = display_text(label), display_text(prefix)
    if not prefix or not label.startswith(prefix):
        return False
    rest = label[len(prefix):]
    return not rest or rest[0].isspace() or unicodedata.category(rest[0]).startswith('P')


def expected_fields(args):
    values = {key: getattr(args, key) for key in ('title', 'notes', 'duration', 'priority', 'tags')
              if getattr(args, key, None) is not None}
    if 'priority' in values:
        values['priority'] = PRIORITIES[values['priority']]
    if 'tags' in values:
        values['tags'] = sorted(set(tag.strip() for tag in values['tags'].split(',') if tag.strip()))
    return values


def matches(task, expected):
    return all((sorted(task[key]) if key == 'tags' else task[key]) == value
               for key, value in expected.items())


def ensure_unique(tasks, task):
    duplicates = [other for other in tasks if other['status'] != 'deleted' and
                  (label_prefix(other['title'], task['title']) or label_prefix(task['title'], other['title']))]
    if len(duplicates) != 1:
        raise RuntimeError('AMBIGUOUS: task titles cannot be distinguished in the UI; rename them in Bluebird before control.')
