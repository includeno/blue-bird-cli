import os
import unittest
from unittest.mock import Mock, patch

from bluebird_cli.domain import display_text, label_prefix
from bluebird_cli.localization import ANCHORS, Catalog, STRINGS
from bluebird_cli.macos import Bridge
from bluebird_cli.ui import BluebirdUI, CONTROLS, selector


def metadata():
    # Invented labels exercise scripts and punctuation without redistributing app translations.
    return {'localizations': {'en': {}, 'ja': {key: '日本語 ' + str(i) for i, (key, _) in enumerate(STRINGS.values())},
                              'ar': {key: '\u200fعربي ' + str(i) for i, (key, _) in enumerate(STRINGS.values())}},
            'preferred_localizations': ['en']}


def anchors(catalog, locale):
    return [{'role': roles[0], 'description': catalog.resolve(locale, semantic)}
            for semantic, roles in ANCHORS.items()]


def check_contract(test, data):
    for locale in data['localizations']:
        with test.subTest(locale=locale):
            catalog = Catalog(data, locale)
            test.assertEqual(catalog.detect(anchors(catalog, locale)), locale)
            automatic = Catalog(dict(data, preferred_localizations=[locale]))
            test.assertEqual(automatic.detect(anchors(catalog, locale)), locale)
            ui = BluebirdUI(Mock(), catalog)
            for control, (roles, ids, semantics) in CONTROLS.items():
                label = catalog.labels(*semantics)[0] if semantics else ''
                node = {'role': roles[0], 'description': label + ('، #example' if control == 'tags' else ''), 'path': [0, 1]}
                if semantics:
                    test.assertIs(ui.choose(control, [node]), node, control)
                if ids:
                    node = dict(node, identifier=ids[0], description='')
                    test.assertIs(ui.choose(control, [node]), node, control)
            for role in ('AXStaticText', 'AXGenericElement'):
                for delimiter in (', ', '，', '、', '، ', ' • '):
                    row = {'role': role, 'description': 'cafe\u0301 👩‍💻' + delimiter + 'metadata',
                           'actions': [{'name': 'dynamic:complete', 'description': catalog.labels('mark_complete')[0]}]}
                    test.assertIs(ui.task_row({'title': 'café 👩‍💻'}, [row]), row)
                    ui.custom(row, 'mark_complete')
                    test.assertEqual(ui.bridge.call.call_args.kwargs['action'], 'dynamic:complete')


class LocalizationTest(unittest.TestCase):
    def test_semantic_contract(self):
        check_contract(self, metadata())

    def test_unicode_normalization_preserves_emoji(self):
        self.assertEqual(display_text('\u200f cafe\u0301\u00a0👩‍💻 '), 'café 👩‍💻')
        self.assertTrue(label_prefix('task، metadata', 'task'))
        self.assertFalse(label_prefix('taskmaster', 'task'))
        self.assertFalse(label_prefix('anything', ''))

    def test_locale_mismatch_and_no_evidence_fail(self):
        catalog = Catalog(metadata(), 'ja')
        with self.assertRaisesRegex(RuntimeError, 'LOCALE_MISMATCH'):
            catalog.detect(anchors(catalog, 'ar'))
        with self.assertRaisesRegex(RuntimeError, 'LOCALE_UNDETECTED'):
            catalog.detect([{'role': 'AXButton', 'description': 'Title'}])
        with self.assertRaises(ValueError): Catalog(metadata(), 'missing')

    def test_variant_fallback_and_alias(self):
        data = metadata()
        data['localizations']['ja-JP'] = {}
        catalog = Catalog(data, 'ja_jp')
        self.assertEqual(catalog.resolve('ja-JP', 'save'), catalog.resolve('ja', 'save'))
        self.assertEqual(catalog.detect(anchors(catalog, 'ja')), 'ja-JP')
        self.assertEqual(catalog.resolve('en', 'discard_progress'), 'Discard Current Progress')

    def test_conflicting_variants_require_choice(self):
        data = {'localizations': {'aa': {'Save': 'A'}, 'bb': {'Save': 'B'}}, 'preferred_localizations': []}
        catalog = Catalog(data)
        with self.assertRaisesRegex(RuntimeError, 'LOCALE_AMBIGUOUS'):
            catalog.detect([{'role': 'AXTextField', 'description': 'Title'}])

    def test_detected_locale_survives_partial_evidence(self):
        data = {'localizations': {'aa': {'Title': 'AA', 'Save': 'A'}, 'bb': {'Title': 'BB', 'Save': 'B'}},
                'preferred_localizations': []}
        catalog = Catalog(data)
        self.assertEqual(catalog.detect([{'role': 'AXTextField', 'description': 'AA'}]), 'aa')
        self.assertEqual(catalog.detect([{'role': 'AXMenuItem', 'title': 'Today'}]), 'aa')
        self.assertEqual(catalog.detect([{'role': 'AXTextField', 'description': 'BB'}]), 'bb')

    def test_stable_id_priority_and_ambiguity(self):
        catalog = Catalog(metadata(), 'en')
        catalog.detect(anchors(catalog, 'en'))
        ui = BluebirdUI(Mock(), catalog)
        node = {'role': 'AXButton', 'identifier': 'plus', 'description': 'unlabelled', 'path': [1, 2]}
        other = {'role': 'AXButton', 'description': 'New Tag'}
        self.assertIs(ui.choose('new_tag', [other, node]), node)
        self.assertEqual(selector(node), node)
        with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS'): ui.choose('new_tag', [node, node])
        with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS'): ui.choose('save', [{'role': 'AXButton', 'description': 'Save'}] * 2)

    def test_system_back_uses_navigation_relationship_not_translation(self):
        catalog = Catalog(metadata(), 'en')
        catalog.detect(anchors(catalog, 'en'))
        ui = BluebirdUI(Mock(), catalog)
        back = {'role': 'AXButton', 'description': 'Précédent', 'path': [0, 5, 0, 0]}
        plus = {'role': 'AXButton', 'identifier': 'plus', 'path': [0, 5, 0, 2]}
        tag_named_back = {'role': 'AXButton', 'description': 'Back', 'path': [0, 5, 1, 0]}
        nodes = [{'role': 'AXPopover', 'path': [0, 5]}, back, plus, tag_named_back]
        self.assertIs(ui.choose('back', nodes), back)
        with self.assertRaisesRegex(RuntimeError, 'structure changed'):
            ui.choose('back', nodes + [dict(back, path=[0, 5, 0, 3])])

    def test_notes_use_real_unicode_input(self):
        ui = BluebirdUI(Mock(), Mock())
        with patch.object(ui, 'find', return_value={'role': 'AXTextArea', 'path': [1]}), patch('bluebird_cli.ui.time.sleep'):
            ui.set_field('notes', '第一行\nعربي 😀')
        self.assertEqual(ui.bridge.call.call_args.args[0], 'type')
        self.assertEqual(ui.bridge.call.call_args.kwargs['value'], '第一行\nعربي 😀')

    def test_retry_only_when_transport_did_not_act(self):
        ui = BluebirdUI(Mock(), Mock())
        ui.bridge.call.side_effect = [RuntimeError('Expected one UI element, found 0; refresh the UI snapshot'), {'ok': True}]
        with patch.object(ui, 'find', return_value={'role': 'AXButton', 'path': [1]}), patch.object(ui, 'snapshot', return_value=[{'role': 'AXButton', 'path': [2]}]), patch('bluebird_cli.ui.time.sleep'):
            self.assertEqual(ui.press('back'), {'ok': True})
            self.assertEqual(ui.bridge.call.call_count, 2)
            ui.bridge.call.reset_mock()
            ui.bridge.call.side_effect = RuntimeError('AX action failed')
            with self.assertRaisesRegex(RuntimeError, 'AX action failed'): ui.press('back')
            self.assertEqual(ui.bridge.call.call_count, 1)

    def test_stale_target_never_retargets_ambiguous_or_changed_state(self):
        original = {'role': 'AXButton', 'description': 'tag', 'path': [1], 'selected': True}
        for nodes in ([dict(original, path=[2]), dict(original, path=[3])],
                      [dict(original, path=[2], selected=False)]):
            ui = BluebirdUI(Mock(), Mock())
            ui.bridge.call.side_effect = RuntimeError('Expected one UI element, found 0; refresh')
            with patch.object(ui, 'snapshot', return_value=nodes), patch('bluebird_cli.ui.time.sleep'):
                with self.assertRaisesRegex(RuntimeError, 'no retry'): ui.action(original)
            self.assertEqual(ui.bridge.call.call_count, 1)

    @unittest.skipUnless(os.environ.get('BLUEBIRD_TEST_APP'), 'Opt-in installed app resource matrix')
    def test_installed_app_all_localizations(self):
        data = Bridge().resources(os.environ['BLUEBIRD_TEST_APP'])
        self.assertGreater(len(data['localizations']), 1)
        check_contract(self, data)


if __name__ == '__main__': unittest.main()
