
import sublime
import sublime_plugin
from collections import OrderedDict
import pprint
import re
import subprocess
import tempfile
import os
try:
    from.Edit import Edit as Edit
except:
    from Edit import Edit as Edit
__ST3 = int(sublime.version()) >= 3000
import shutil
import json
if __ST3:
    import Pandown.minify_json as minify_json
else:
    import minify_json

DEBUG_MODE = True

def debug(theMessage):

    if DEBUG_MODE:
        print("Spandoc: " + str(theMessage))

def err(e):
    print("Spandoc ERROR: " + str(e))

class PromptPandocCommand(sublime_plugin.WindowCommand):

    '''Defines the plugin command palette item.'''


    options = []

    def run(self):

        # return view, folder_path and filename from the current window
        view, folder_path, file_name = get_current(self.window)

        # get the user settings:
        settings = get_settings(view, folder_path, file_name)

        self.transformation_list = self.get_transformation_list(settings, self.window)
        self.window.show_quick_panel(self.transformation_list, self.picked_transformation)


    def get_transformation_list(self, settings, window):
        '''Generates a ranked list of available transformations.'''

        # returns the currently edited view.
        view = window.active_view()

        # score the transformations and rank them
        ranked = {}
        for label, setting in settings['transformations'].items():
            for scope in setting['scope'].keys():
                score = view.score_selector(0, scope)
                if not score:
                    continue
                if label not in ranked or ranked[label] < score:
                    ranked[label] = score

        if not len(ranked):
            sublime.error_message(
                'No transformations configured for the syntax '
                + view.settings().get('syntax'))
            return

        # reverse sort
        self.options = list(OrderedDict(sorted(
            ranked.items(), key=lambda t: t[1])).keys())
        self.options.reverse()

        return self.options


    def picked_transformation(self, i):
        ''' pass the name of the picked_transformation to the pandoc command and execute'''
        if i == -1:
            return

        # get the name of the picked_transformation from the selected item "i":
        picked_transformation = self.transformation_list[i]

        # execute the pandoc command with passing the wanted/picked transformation
        self.window.run_command('pandoc', {'transformation': picked_transformation })


class BuildPandocCommand(sublime_plugin.WindowCommand):

    def run(self, transformation):

        # you need a BuildPandocCommand and you execute the PandocCommand directly with the build_system and passing transformation,
        # because it must be a Sublime WindowCommand and no TextCommand like it is in the PandocCommand
        self.window.active_view().run_command('pandoc', {'transformation': transformation })



class PandocCommand(sublime_plugin.WindowCommand):

    '''Transforms using Pandoc.'''

    def run(self, transformation):

        # return currently edited view, dir and filename from the window
        view, folder_path, file_name = get_current(self.window)

        # get the user settings:
        settings = get_settings(view, folder_path, file_name)

        # get all the items from picked transformation out of the settings
        transformation = settings['transformations'][transformation]

        # string to work with
        region = sublime.Region(0, view.size())
        contents = view.substr(region)

        # pandoc executable
        binary_name = 'pandoc.exe' if sublime.platform() == 'windows' else 'pandoc'
        pandoc = _find_binary(binary_name, settings['pandoc-path'])
        if pandoc is None:
            return
        cmd = [pandoc]

        # from format
        score = 0
        for scope, c_iformat in transformation['scope'].items():
            c_score = view.score_selector(0, scope)
            if c_score <= score:
                continue
            score = c_score
            iformat = c_iformat
        cmd.extend(['-f', iformat])

        # configured parameters
        args = Args(transformation['pandoc-arguments'])
        # Use pandoc output format name as file extension unless specified by out-ext in transformation
        try:
            transformation['out-ext']
        except:
            argsext = None
        else:
            argsext = transformation['out-ext']
        # output format
        oformat = args.get(short=['t', 'w'], long=['to', 'write'])
        oext = argsext

        # pandoc doesn't actually take 'pdf' as an output format
        # see https://github.com/jgm/pandoc/issues/571
        if oformat == 'pdf':
            args = args.remove(
                short=['t', 'w'], long=['to', 'write'], values=['pdf'])

        # output file locally
        try:
            transformation['out-local']
        except:
            argslocal = None
        else:
            argslocal = transformation['out-local']

        # if write to file, add -o if necessary, set file path to output_path
        output_path = None
        if oformat is not None and oformat in settings['pandoc-format-file']:
            output_path = args.get(short=['o'], long=['output'])
            if output_path is None:
                # note the file extension matches the pandoc format name
                if argslocal and file_name:
                    output_path = file_name
                else:
                    output_path = tempfile.NamedTemporaryFile().name
                # If a specific output format not specified in transformation, default to pandoc format name
                if oext is None:
                    output_path += "." + oformat
                else:
                    output_path += "." + oext
                args.extend(['-o', output_path])

        cmd.extend(args)

        # run pandoc

        sublime.set_timeout_async(lambda: self.pass_to_pandoc(cmd, folder_path, contents, oformat, transformation, output_path), 0)

        # write pandoc command to console
        # print(' '.join(cmd))


    def pass_to_pandoc(self, cmd, folder_path, contents, oformat, transformation, output_path):
        process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder_path)
        result, error = process.communicate(contents.encode('utf-8'))  # always waits for the output (buffering). But this is not a problem in a threaded enviroment like sublime.set_timeout_async!

        # handle pandoc errors
        if error:
            sublime.error_message('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))
            # print('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))  # just display errors in the console windows
            return

        # if write to file, open
        # if oformat is not None and oformat in get_settings('pandoc-format-file'):
        #     try:
        #         if sublime.platform() == 'osx':
        #             subprocess.call(["open", output_path])
        #         elif sublime.platform() == 'windows':
        #             os.startfile(output_path)
        #         elif os.name == 'posix':
        #             subprocess.call(('xdg-open', output_path))
        #     except:
        #         sublime.message_dialog('Wrote to file ' + output_path)
        #     return

        # write to buffer
        if result:
            if transformation['new-buffer']:
                w = self.view.window()
                w.new_file()
                view = w.active_view()
                region = sublime.Region(0, view.size())
            else:
                view = self.view
                region = sublime.Region(0, view.size())

            with Edit(view) as edit:
                edit.replace(region, result.decode('utf8').replace('\r\n','\n'))

            view.set_syntax_file(transformation['syntax_file'])

        # Output Status message done:
        sublime.status_message("🚩🚩🚩 Pandoc DONE 🚩🚩🚩")

def _find_binary(name, default=None):
    '''Returns a configure path or looks for an executable on the system path.
    '''

    if default is not None:
        if os.path.exists(default):
            return default
        msg = 'configured path for {0} {1} not found.'.format(name, default)
        sublime.error_message(msg)
        return None

    for dirname in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(dirname, name)
        if os.path.exists(path):
            return path

    sublime.error_message('Could not find pandoc executable on PATH.')
    return None


def get_current(window):

    # returns the currently edited view.
    view = window.active_view()

    # get current file path:
    current_file_path = view.file_name()
    debug("current file path: " + current_file_path)
    if current_file_path:
        folder_path, file_name = os.path.split(current_file_path)
    else:
        folder_path = file_name = None

    return (view, folder_path, file_name)


def get_settings(view, folder_path=None, file_name=None):
    '''Return a settings file with the highest precedence:
    1. Is the settings file an absolute file path?
    2. Is the settings file in the current folder path?
    3. Is the settings file somewhere in the project?
    '''

    # 1. Search for a folder settings file
    folder_settings_file = search_for_folder_settings_file("spandoc.json", folder_path, view.window())

    if folder_settings_file:
        settings = load_folder_settings_file(folder_settings_file)
        print("settings after load: ")
        print(settings)

        # default = sublime.load_settings('Pandoc.sublime-settings')
        # default = default.get('default', {})
        # print("default")
        # print(default)



    # if there is no folder_settings_file use the user_settings_file
    else:

        settings = sublime.load_settings('Pandoc.sublime-settings')

        # print("settings")
        # print(settings)

        settings = settings.get('default', {})



        # print("default")
        # print(default)

        # user = settings.get('user', {})

        # if user:

        #     # merge each transformation
        #     transformations = default.pop('transformations', {})
        #     user_transformations = user.get('transformations', {})
        #     for name, data in user_transformations.items():
        #         if name in transformations:
        #             transformations[name].update(data)
        #         else:
        #             transformations[name] = data
        #     default['transformations'] = transformations
        #     user.pop('transformations', None)

        #     # merge all other keys
        #     default.update(user)

    return settings




def load_folder_settings_file(folder_settings_file):

    try:
        folder_settings_file = open(folder_settings_file, "r")
    except IOError as e:
        sublime.status_message("Error: pandoc-config exists, but could not be read.")
        err("Spandoc Exception: " + str(e))
        folder_settings_file.close()
    else:
        settings_file_commented = folder_settings_file.read()
        # print("settings_file_commented:")
        # print(settings_file_commented)
        folder_settings_file.close()
        settings_file = minify_json.json_minify(settings_file_commented)
        print("settings_file before json.loads:")
        print(settings_file)
        try:
            settings_file = json.loads(settings_file)
            print("settings_file afetr json.loads")
            print(settings_file)

        except (KeyError, ValueError) as e:
            sublime.status_message("JSON Error: Cannot parse spandoc.json. See console for details.")
            err("uSpandoc Exception: " + str(e))
            return None
        if "default" in settings_file:
            settings = settings_file["default"]
            print("settings Default")
            print(settings)

    return settings



def search_for_folder_settings_file(file_name, folder_path, window=None):
    '''
    1. Is the settings file an absolute file path?
    2. Is the settings file in the current folder path?
    3. Is the settings file somewhere in the project?
    '''

    # 1. Is the settings file an absolute file path?
    # NOT IMPLEMENTED YET !!!!!!!
    # debug("Is the settings file \"" + file_name + "\" an absolute file path?")
    # file_path = os.path.abspath(os.path.expanduser(file_name))
    # if os.path.isfile(file_path):
        # debug("The settings file \"" + file_name + "\" is an absolute file path!")
    #     return file_path

    # 2. Is the settings file in the current folder path?
    debug("Is the settings file \"" + file_name + "\" in the current folder path?")
    folder_path_settings_file = os.path.join(folder_path, file_name)
    if os.path.exists(folder_path_settings_file):
        debug("Yes!")
        return folder_path_settings_file
    debug("No!")

    # 3. Is the settings file somewhere in the project?
    debug("Is the settings file \"" + file_name + "\" somewhere in the project?")
    # if search_in_project
    project_folders = window.folders()
    # debug("(Searching the following folders and their subfolders: " + str(project_folders) + ")")
    if project_folders:
        unused_head, folder_name = os.path.split(folder_path)
        # debug("folder_name: " + folder_name)
        located_folder_path = None
        for folder in project_folders:
            for root, dirs, files in os.walk(folder, topdown=False):
                # debug("files: " + str(files))
                # debug("root: " + root)

                # unused_roothead, root_tail = os.path.split(root)
                # debug("root_tail " + root_tail)
                for file in files:
                    pass
                    # debug("file_name: " + file_name)
                    if file == file_name:
                        # print("**************************")
                        # debug("dirs:"+ str(dirs))
                        # debug("dirs:"+ str(root))
                        located_folder_path = root
                # for name in dirs:
                #     # debug("name: " + name)
                #     if name == folder_name:
                #         located_folder_path = folder
        # debug("located_folder_path: " + located_folder_path)
        # checkDIR = folder_path
        # debug("Initial checkDIR: " + checkDIR)
        if located_folder_path:
            folder_settings_file = os.path.join(located_folder_path, file_name)
            if os.path.exists(folder_settings_file):
                debug("Yes!")
                debug("It's in this folder: " + folder_settings_file)
                return folder_settings_file
        else:
            debug("No!")
            return None



def _c(item):
    '''Pretty prints item to console.'''
    pprint.PrettyPrinter().pprint(item)


class Args(list):

    '''Process Pandoc arguments.

    "short" are of the form "-k val""".
    "long" arguments are of the form "--key=val""".'''

    def get(self, short=None, long=None):
        '''Get the first value for a argument.'''
        value = None
        for arg in self:
            if short is not None:
                if value:
                    return arg
                match = re.search('^-(' + '|'.join(short) + ')$', arg)
                if match:
                    value = True  # grab the next arg
                    continue
            if long is not None:
                match = re.search('^--(' + '|'.join(long) + ')=(.+)$', arg)
                if match:
                    return match.group(2)
        return None

    def remove(self, short=None, long=None, values=None):
        '''Remove all matching arguments.'''
        ret = Args([])
        value = None
        for arg in self:
            if short is not None:
                if value:
                    if values is not None and arg not in values:
                        ret.append(arg)
                    value = None
                    continue
                match = re.search('^-(' + '|'.join(short) + ')$', arg)
                if match:
                    value = True  # grab the next arg
                    continue
            if long is not None:
                match = re.search('^--(' + '|'.join(long) + ')=(.+)$', arg)
                if match:
                    continue
            ret.append(arg)
        return ret
