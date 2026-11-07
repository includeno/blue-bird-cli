"""Resolve semantic controls using the installed app's localization resources."""
from .domain import display_text

# Each entry is (Bluebird resource key, development-language default).
# Defaults are source strings, not a separately maintained translation catalog.
STRINGS = {
    'title': ('Title', 'Title'),
    'notes': ('Notes', 'Notes'),
    'task_duration': ('task.duration', 'Duration'),
    'priority': ('Priority', 'Priority'),
    'tags': ('Tags', 'Tags'),
    'tag_name': ('Tag Name', 'Tag Name'),
    'new_tag': ('new-tag.verb', 'New Tag'),
    'today': ('sidebar.today', 'Today'),
    'completed': ('sidebar.completed', 'Completed'),
    'scheduled': ('sidebar.scheduled', 'Scheduled'),
    'settings': ('sidebar.settings', 'Settings'),
    'mark_complete': ('Mark as Completed', 'Mark as Completed'),
    'mark_incomplete': ('Mark as Incomplete', 'Mark as Incomplete'),
    'delete': ('Delete', 'Delete'),
    'focus': ('Focus', 'Focus'),
    'save': ('Save', 'Save'),
    'clear': ('Clear', 'Clear'),
    'done': ('Done', 'Done'),
    'back': ('Back', 'Back'),
    'discard_progress': ('Discard Current Progress', 'Discard Current Progress'),
    'session_duration': ('Session Duration', 'Session Duration'),
    'hour': ('duration-picker.hour.singular', 'hour'),
    'hours': ('duration-picker.hour.plural', 'hours'),
    'minute': ('duration-picker.minute.singular', 'min'),
    'minutes': ('duration-picker.minute.plural', 'min'),
    'start': ('Start', 'Start'),
    'stop': ('Stop', 'Stop'),
    'finish': ('Finish Early', 'Finish Early'),
}

# Role-qualified evidence avoids treating a task/tag named "Save" as a language signal.
ANCHORS = {
    'today': ('AXMenuItem',), 'completed': ('AXMenuItem',),
    'scheduled': ('AXMenuItem',), 'settings': ('AXStaticText',),
    'title': ('AXTextField',), 'notes': ('AXTextArea',),
    'session_duration': ('AXSlider',), 'priority': ('AXSlider',),
}


def language_id(value):
    return value.replace('_', '-').lower()


class Catalog:
    def __init__(self, metadata, requested='auto'):
        self.metadata = metadata
        self.tables = metadata['localizations']
        if not self.tables:
            raise RuntimeError('Bluebird localization resources are missing')
        self.requested = requested
        self.selected = None
        self.by_id = {language_id(name): name for name in self.tables}
        self.preferred = metadata.get('preferred_localizations', [])
        if requested != 'auto' and language_id(requested) not in self.by_id:
            raise ValueError(f'Unsupported locale {requested}; available: {", ".join(sorted(self.tables))}')

    def resolve(self, locale, semantic):
        key, default = STRINGS[semantic]
        table = self.tables[locale]
        value = table.get(key)
        # Region variants inherit a base localization when one is shipped.
        base = self.by_id.get(language_id(locale).split('-')[0])
        if not value and base and base != locale:
            value = self.tables[base].get(key)
        return value or self.tables.get('en', {}).get(key) or default

    def detect(self, nodes):
        scores = {}
        for locale in self.tables:
            scores[locale] = sum(
                any(node.get('role') in roles and any(
                    display_text(node.get(field, '')) == display_text(self.resolve(locale, semantic))
                    for field in ('description', 'title')) for node in nodes)
                for semantic, roles in ANCHORS.items())
        best = max(scores.values())
        if best == 0:
            raise RuntimeError('LOCALE_UNDETECTED: no Bluebird language anchors are visible; open its main window')
        candidates = [locale for locale, score in scores.items() if score == best]
        if self.requested != 'auto':
            selected = self.by_id[language_id(self.requested)]
            if selected not in candidates:
                raise RuntimeError(f'LOCALE_MISMATCH: requested {selected}, observed {", ".join(candidates)}')
        else:
            preference = ([self.selected] if self.selected else []) + self.preferred + sorted(candidates)
            selected = next(locale for locale in preference if locale in candidates)
            # Identical region variants are safe; conflicting translations require an explicit choice.
            signatures = {tuple(self.resolve(locale, key) for key in STRINGS) for locale in candidates}
            if len(signatures) > 1 and selected not in self.preferred and selected != self.selected and len(candidates) > 1:
                raise RuntimeError(f'LOCALE_AMBIGUOUS: choose --locale from {", ".join(candidates)}')
        self.selected = selected
        return selected

    def labels(self, *semantics):
        if self.selected is None:
            raise RuntimeError('Language must be detected from the UI before resolving controls')
        return tuple(dict.fromkeys(self.resolve(self.selected, key) for key in semantics))

    def report(self):
        return {'available': sorted(self.tables), 'selected': self.selected, 'requested': self.requested,
                'source': 'installed_app_bundle', 'app_version': self.metadata.get('version'),
                'fallbacks': {locale: [semantic for semantic, (key, _) in STRINGS.items()
                                       if key not in table]
                              for locale, table in self.tables.items()}}
