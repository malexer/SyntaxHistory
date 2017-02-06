import sys
from unittest.mock import Mock, MagicMock

from pytest import fixture


sublime = MagicMock()
sublime_plugin = MagicMock()
sys.modules['sublime'] = sublime
sys.modules['sublime_plugin'] = sublime_plugin


DEFAULT_DATA = [
    ('f1', 's1'),
    ('f2', 's2'),
    ('f3', 's3'),
]


@fixture
def sublime_settings():
    settings = MagicMock()
    sublime.load_settings = Mock(side_effect=lambda x: settings)

    settings.get.side_effect = lambda self, key: DEFAULT_DATA[:]
    return settings


@fixture
def history(sublime_settings):
    from syntax_history import History

    return History(history_filename='HISTORY_FILENAME', max_items=4)


class TestHistory(object):

    def test_load_file_on_init(self, history):
        sublime.load_settings.assert_called_with('HISTORY_FILENAME')
        assert list(history.data.items()) == DEFAULT_DATA

    def test_add_item_and_save(self, sublime_settings, history):
        history['f4'] = 's4'

        expected_stored_items = [
            ('f1', 's1'),
            ('f2', 's2'),
            ('f3', 's3'),
            ('f4', 's4'),
        ]

        assert list(history.data.items()) == expected_stored_items
        sublime_settings.set.assert_called_with(
            'history', expected_stored_items)

        sublime.save_settings.assert_called_with('HISTORY_FILENAME')

    def test_del_item_and_save(self, sublime_settings, history):
        del history['f2']

        expected_stored_items = [
            ('f1', 's1'),
            ('f3', 's3'),
        ]

        assert list(history.data.items()) == expected_stored_items
        sublime_settings.set.assert_called_with(
            'history', expected_stored_items)

        sublime.save_settings.assert_called_with('HISTORY_FILENAME')

    def test_size_limit(self, sublime_settings, history):
        history['f4'] = 's4'
        assert list(history.data.items()) == [
            ('f1', 's1'), ('f2', 's2'), ('f3', 's3'), ('f4', 's4')]

        history['f5'] = 's5'
        assert list(history.data.items()) == [
            ('f2', 's2'), ('f3', 's3'), ('f4', 's4'), ('f5', 's5')]

        history['f6'] = 's6'
        assert list(history.data.items()) == [
            ('f3', 's3'), ('f4', 's4'), ('f5', 's5'), ('f6', 's6')]

    def test_size_limit_with_lru_logic(self, sublime_settings, history):
        'f2' in history  # should not change order
        assert list(history.data.items()) == [
            ('f1', 's1'), ('f2', 's2'), ('f3', 's3')]

        # LRU logic
        history['f2']
        assert list(history.data.items()) == [
            ('f1', 's1'), ('f3', 's3'), ('f2', 's2')]

        history['f1']
        assert list(history.data.items()) == [
            ('f3', 's3'), ('f2', 's2'), ('f1', 's1')]

        history['f4'] = 's4'
        assert list(history.data.items()) == [
            ('f3', 's3'), ('f2', 's2'), ('f1', 's1'), ('f4', 's4')]

        history['f5'] = 's5'
        assert list(history.data.items()) == [
            ('f2', 's2'), ('f1', 's1'), ('f4', 's4'), ('f5', 's5')]

        history['f1']
        assert list(history.data.items()) == [
            ('f2', 's2'), ('f4', 's4'), ('f5', 's5'), ('f1', 's1')]

        history['f6'] = 's6'
        assert list(history.data.items()) == [
            ('f4', 's4'), ('f5', 's5'), ('f1', 's1'), ('f6', 's6')]

        history['f7'] = 's7'
        assert list(history.data.items()) == [
            ('f5', 's5'), ('f1', 's1'), ('f6', 's6'), ('f7', 's7')]
