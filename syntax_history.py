from collections import UserDict

import sublime
import sublime_plugin


SYNTAX_HISTORY_FILE = 'SyntaxHistory.sublime-settings'


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

    def __init__(self, history_filename):
        self.filename = history_filename
        self.settings = sublime.load_settings(history_filename)

        initial_data = {}
        if self.settings.has('history'):
            initial_data = self.settings.get('history')

        super().__init__(initial_data)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.save()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def save(self):
        self.settings.set('history', self.data)
        sublime.save_settings(self.filename)


class SyntaxHistoryEventListener(sublime_plugin.EventListener):

    def on_post_text_command(self, view, command_name, args):
        if command_name == 'set_file_type':
            syntax = args.get('syntax')
            if syntax:
                filename = view.file_name()
                if filename is not None:
                    history = History(SYNTAX_HISTORY_FILE)
                    history[filename] = syntax

    def on_load_async(self, view):
        filename = view.file_name()
        history = History(SYNTAX_HISTORY_FILE)

        if filename in history:
            syntax = history[filename]

            if syntax_exists(syntax):
                view.set_syntax_file(syntax)
            else:
                del history[filename]
