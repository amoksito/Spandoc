from __future__ import print_function
import sublime
import sublime_plugin
import os
import shutil
import codecs


class PandocTouchProjectConfigCommand(sublime_plugin.WindowCommand):
    def run(self):
        if self.window.active_view().file_name():
            configFile = os.path.join(os.path.dirname(self.window.active_view().file_name()), 'pandoc-config.json')
        else:
            sublime.status_message("Cannot create project configuration for unsaved files.")
            return

        if os.path.exists(configFile):
            self.window.open_file(configFile)
            return

        defaultConfigFile = os.path.join(sublime.packages_path(), 'sublimetext-pandoc', 'pandoc.sublime-settings')
        userConfigFile = os.path.join(sublime.packages_path(), 'User', 'pandoc-config.json')

        if not os.path.exists(defaultConfigFile) and not os.path.exists(userConfigFile):
            try:
                s = sublime.load_resource("packages\sublimetext-pandoc\pandoc.sublime-settings")
            except OSError as e:
                sublime.status_message("Could not load default Pandoc configuration.")
                print("[Pandoc could not find a default configuration file in Packages/Pandoc/pandoc.sublime-settings]")
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
                print("[Pandoc encountered an exception:]")
                print("[e: {0}]".format(e))
            else:
                self.window.open_file(configFile)
