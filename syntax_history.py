from collections import OrderedDict, UserDict

import sublime
import sublime_plugin


# max count of history items to keep
HISTORY_MAX_SIZE = 1000

HISTORY_FILE = 'SyntaxHistory.sublime-settings'


def syntax_exists(package_based_path):
    """Check if syntax file exists.

    :type package_based_path: str
    :param package_based_path: syntax file specified in Sublime Text's
                               packages format.

    .. note::
        Sublime Text specifies syntax file path in format::

            Packages/Python/Python.sublime-syntax
            Packages/User/Python-custom.sublime-syntax

    """

    try:
        sublime.load_binary_resource(package_based_path)
        return True
    except OSError:
        return False


class History(UserDict):
    """Access syntax history as a dict, persist it to .sublime-settings
    file.
    """

    def __init__(self, history_filename, max_items=1000):
        self.filename = history_filename
        self.max_items = max_items
        self.load()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.save()

    def __getitem__(self, key):
        self.data.move_to_end(key)  # LRU logic
        self.save()
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def apply_size_limit(self):
        while len(self.data) > self.max_items:
            self.data.popitem(last=False)

    def load(self):
        self.settings = sublime.load_settings(self.filename)
        data = self.settings.get('history', [])

        if isinstance(data, dict):  # support loading old config
            data = list(data.items())

        self.data = OrderedDict(data)

    def save(self):
        self.apply_size_limit()

        self.settings.set('history', list(self.data.items()))
        sublime.save_settings(self.filename)


class SyntaxHistoryEventListener(sublime_plugin.EventListener):

    def on_post_text_command(self, view, command_name, args):
        if command_name == 'set_file_type':
            syntax = args.get('syntax')
            if syntax:
                filename = view.file_name()
                if filename is not None:
                    history = History(HISTORY_FILE, max_items=HISTORY_MAX_SIZE)
                    history[filename] = syntax

    def on_load_async(self, view):
        filename = view.file_name()
        history = History(HISTORY_FILE, max_items=HISTORY_MAX_SIZE)

        if filename in history:
            syntax = history[filename]

            if syntax_exists(syntax):
                view.set_syntax_file(syntax)
            else:
                del history[filename]
