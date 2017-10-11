from __future__ import print_function
import sublime
import sublime_plugin
import os
import shutil
import codecs


class SpandocConfigCommand(sublime_plugin.WindowCommand):
    def run(self):
        if self.window.active_view().file_name():
            configFile = os.path.join(os.path.dirname(self.window.active_view().file_name()), 'spandoc.json')
        else:
            sublime.status_message("Cannot create project configuration for unsaved files.")
            return

        if os.path.exists(configFile):
            self.window.open_file(configFile)
            return

        defaultConfigFile = os.path.join(sublime.packages_path(), 'spandoc', 'Spandoc.sublime-settings')
        userConfigFile = os.path.join(sublime.packages_path(), 'User', 'Spandoc.sublime-settings')

        if not os.path.exists(defaultConfigFile) and not os.path.exists(userConfigFile):
            try:
                s = sublime.load_resource("packages\spandoc\Spandoc.sublime-settings")
            except OSError as e:
                sublime.status_message("Could not load default Pandoc configuration.")
                print("[Spandoc could not find a default configuration file in Packages/Spandoc/Spandoc.sublime-settings]")
                print("[Loading from the binary package resource file also failed.]")
                print("[e: {0}]".format(e))
                return
            with codecs.open(configFile, "w", "utf-8") as f:
                f.write(s)
            self.window.open_file(configFile)

        else:
            try:
                toCopy = defaultConfigFile if not os.path.exists(userConfigFile) else userConfigFile
                shutil.copy(toCopy, configFile)
            except Exception as e:
                sublime.status_message("Could not write {0}".format(configFile))
                print("[Spandoc encountered an exception:]")
                print("[e: {0}]".format(e))
            else:
                self.window.open_file(configFile)
