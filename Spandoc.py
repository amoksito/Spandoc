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

DEBUG_MODE = False

class SpandocPaletteCommand(sublime_plugin.WindowCommand):

    '''Defines the plugin command palette item.'''

    def run(self):

        # return view, folder_path and filename from the current window
        view, folder_path, file_name = get_current(self.window)
        debug("folder_path: " + folder_path)
        debug("file_name: " + file_name)

        # get the user settings:
        settings = get_settings(view, folder_path, file_name)
        debug("settings: " + str(settings))

        # get transformation list for the current view
        self.transformation_list = self.get_transformation_list(settings, view)

        # show the transformation list with Sublimes "Quick Panel", and for the picked transformation the picked_transformation function will be executed, which will then pass the picked transformation to the SpandocCommand
        self.window.show_quick_panel(self.transformation_list, self.picked_transformation)


    def get_transformation_list(self, settings, view):
        '''Generates a ranked list of available transformations.'''

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
            sublime.error_message('No transformations configured for the syntax '+ view.settings().get('syntax'))

            return

        # reverse sort
        transformation_list = list(OrderedDict(sorted(
            ranked.items(), key=lambda t: t[1])).keys())
        transformation_list.reverse()

        return transformation_list


    def picked_transformation(self, i):
        ''' pass the name of the picked_transformation to the Spandoc command and execute'''
        if i == -1:
            return

        # get the name of the picked_transformation from the selected item "i":
        picked_transformation = self.transformation_list[i]
        debug("picked_transformation: " + picked_transformation)

        # execute the Spandoc command with passing the wanted/picked transformation
        self.window.run_command('spandoc_run', {'transformation': picked_transformation })


class SpandocRunCommand(sublime_plugin.WindowCommand):

    '''Transforms using Spandoc.'''

    def run(self, transformation):

        # return currently edited view, dir and filename from the window
        view, folder_path, file_name = get_current(self.window)

        # get the user settings:
        settings = get_settings(view, folder_path, file_name)

        # get all the items from picked transformation out of the settings
        transformation = settings['transformations'][transformation]
        # debug("transformations: " + str(transformation))

        # string to work with (gets the whole file as text in buffer; selects the whole file)
        region = sublime.Region(0, view.size())
        # debug("region: " + str(region))
        contents = view.substr(region)
        # debug("contents: " + str(contents))

        # pandoc executable
        pandoc_path = settings['pandoc-path']
        if pandoc_path is None:
            sublime.error_message('Could not find pandoc executable. Do you have set the "pandoc-path" parameter in the settings?')
        # debug("pandoc_path: " + str(pandoc_path))
        cmd = [pandoc_path]

        # get pandoc's `--from` parameter:
        # Non-pandoc extensions:  http://pandoc.org/MANUAL.html#non-pandoc-extensions
        score = 0
        for scope, non_pandoc_extensions in transformation['scope'].items():
            c_score = view.score_selector(0, scope)
            # debug("c_score: " + str(c_score))
            if c_score <= score:
                continue
            score = c_score
            # debug("score: " + str(score))
            # debug("non_pandoc_extensions: " + str(non_pandoc_extensions))

        # add the pandoc's `--from` parameter:
        cmd.extend(['-f', non_pandoc_extensions])
        # debug("cmd: " + str(cmd))

        pandoc_arguments = transformation['pandoc-arguments']
        # debug("pandoc_arguments: " + str(pandoc_arguments))
        # it is not really clear for me, why we need the process_pandoc_arguments function?
        args = process_pandoc_arguments(pandoc_arguments)
        # debug("args: " + str(args))


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
        # see https://github.com/jgm/Spandoc/issues/571
        if oformat == 'pdf':
            args = args.remove(
                short=['t', 'w'], long=['to', 'write'], values=['pdf'])

        # output file locally
        try:
            transformation['out-local']
        except:
            out_local = None
        else:
            out_local = transformation['out-local']

        # if write to file, add -o if necessary, set file name to output name
        # but the file name needs to be without an extension. the extension will be added in accordance with the to/output format
        file_name, file_extension = os.path.splitext(file_name)
        output_name = None
        if oformat is not None and oformat in settings['pandoc-format-file']:
            output_name = args.get(short=['o'], long=['output'])
            # debug("output_name: " + str(output_name))
            if output_name is None:
                # note the file extension matches the pandoc format name
                if out_local and file_name:
                    output_name = file_name
                    # debug("output_name: " + str(output_name))
                else:
                    output_name = tempfile.NamedTemporaryFile().name
                # If a specific output format not specified in transformation, default to pandoc format name
                if oext is None:
                    output_name += "." + oformat
                else:
                    output_name += "." + oext
                # debug("output_name: " + str(output_name))
                args.extend(['-o', output_name])

        cmd.extend(args)

        # run pandoc in async mode
        sublime.set_timeout_async(lambda: self.pass_to_pandoc(cmd, folder_path, contents, oformat, transformation, output_name), 0)

        # write pandoc command to console
        debug("cmd: " + str(cmd))


    def pass_to_pandoc(self, cmd, folder_path, contents, oformat, transformation, output_name):
        process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder_path)
        # Next line always waits for the output (buffering). But this is not a problem in a threaded enviroment like sublime.set_timeout_async!
        result, error = process.communicate(contents.encode('utf-8'))

        # handle Spandoc errors
        if error:
            sublime.error_message('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))
            # print('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))  # just display errors in the console windows
            return

        # if write to file, open
        # if oformat is not None and oformat in get_settings('pandoc-format-file'):
        #     try:
        #         if sublime.platform() == 'osx':
        #             subprocess.call(["open", output_name])
        #         elif sublime.platform() == 'windows':
        #             os.startfile(output_name)
        #         elif os.name == 'posix':
        #             subprocess.call(('xdg-open', output_name))
        #     except:
        #         sublime.message_dialog('Wrote to file ' + output_name)
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
        sublime.status_message("🚩🚩🚩 Spandoc DONE 🚩🚩🚩")


class process_pandoc_arguments(list):

    '''Process pandoc arguments.

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
        ret = process_pandoc_arguments([])
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



################################### Global Functions: ###################################

def debug(theMessage):

    if DEBUG_MODE:
        print("Spandoc: " + str(theMessage))

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
    '''Return a settings file with the highest precedence: '''

    # Search for a folder settings file
    folder_settings_file = search_for_folder_settings_file("spandoc.json", folder_path, view.window())
    # debug("folder_settings_file: " + str(folder_settings_file))


    # if there is a folder_settings_file, load its settings, else use either the user_settings_file or the default_settings_file
    if folder_settings_file:
        settings = load_folder_settings_file(folder_settings_file)
        # debug("settings: " + str(settings))

    else:
        settings = sublime.load_settings('Spandoc.sublime-settings')
        debug("Taking either the user_settings_file (if it exists) or the default_settings_file")
        # debug("settings: " + str(settings))


        # only the default array is needed
        default = settings.get('default')

        # but when there is a user array instead of a default array, then merrge the settings
        user = settings.get('user', {})
        if user:
            # merge each transformation
            transformations = default.pop('transformations', {})
            user_transformations = user.get('transformations', {})
            for name, data in user_transformations.items():
                if name in transformations:
                    transformations[name].update(data)
                else:
                    transformations[name] = data
            default['transformations'] = transformations
            user.pop('transformations', None)

            # merge all other keys
            default.update(user)

        settings = default
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
    project_folders = window.folders()
    debug("(Searching the following folders and their subfolders: " + str(project_folders) + ")")
    if project_folders:
        unused_head, folder_name = os.path.split(folder_path)
        located_folder_path = None
        for folder in project_folders:
            for root, dirs, files in os.walk(folder, topdown=False):
                for file in files:
                    # debug("file_name: " + file_name)
                    if file == file_name:
                        located_folder_path = root
        # debug("located_folder_path: " + located_folder_path)
        if located_folder_path:
            folder_settings_file = os.path.join(located_folder_path, file_name)
            if os.path.exists(folder_settings_file):
                debug("Yes!")
                debug("It's in this folder: " + folder_settings_file)
                return folder_settings_file
        else:
            debug("No!")
            debug("There is no folder settings file")
            return None


def load_folder_settings_file(folder_settings_file):

    try:
        folder_settings_file = open(folder_settings_file, "r")
    except IOError as e:
        sublime.error_message("Error: spandoc.json exists, but could not be read. Exception: " + str(e))
        folder_settings_file.close()
    else:
        settings_file_commented = folder_settings_file.read()
        folder_settings_file.close()
        settings_file = minify_json.json_minify(settings_file_commented)
        debug("settings_file: " + str(settings_file))
        try:
            settings_file = json.loads(settings_file)
        except (KeyError, ValueError) as e:
            sublime.error_message("JSON Error: Cannot parse spandoc.json. See console for details. Exception: " + str(e))
            return None
        if "default" in settings_file:
            settings = settings_file["default"]

    return settings


