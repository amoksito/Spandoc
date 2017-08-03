# Copyright (c) 2012 Brian Fisher
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

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
    from Pandown.pandownCriticPreprocessor import *
else:
    import minify_json
    from pandownCriticPreprocessor import *

def debug(theMessage):

    # if DEBUG_MODE:
    print("[Sublime-Pandoc: " + str(theMessage) + "]")

def err(e):
    print("[Sublime-Pandoc ERRROR: " + str(e) + "]")

class PromptPandocCommand(sublime_plugin.WindowCommand):

    '''Defines the plugin command palette item.

    @see Default.sublime-commands'''

    options = []

    def run(self):

        # get the user settings:
        settings = get_user_settings(self.window)

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
        # because  it must be a Sublime WindowCommand and no TextCommand like it is in the PandocCommand
        self.window.active_view().run_command('pandoc', {'transformation': transformation })



class PandocCommand(sublime_plugin.WindowCommand):

    '''Transforms using Pandoc.'''

    def run(self, transformation):

        # returns the window object
        view = self.window.active_view()

        # get current file path
        current_file_path = view.file_name()
        if current_file_path:
            working_dir = os.path.dirname(current_file_path)
            file_name = os.path.splitext(current_file_path)[0]
        else:
            working_dir = None
            file_name = None

        # get the user settings:
        settings = get_user_settings(self.window, working_dir, file_name)

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

        sublime.set_timeout_async(lambda: self.pass_to_pandoc(cmd, working_dir, contents, oformat, transformation, output_path), 0)

        # write pandoc command to console
        print(' '.join(cmd))


    def pass_to_pandoc(self, cmd, working_dir, contents, oformat, transformation, output_path):
        process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir)
        result, error = process.communicate(contents.encode('utf-8'))  # always waits for the output (buffering). But this is not a problem in a threaded enviroment like sublime.set_timeout_async!

        # handle pandoc errors
        if error:
            sublime.error_message('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))
            # print('\n\n'.join(['Error when running:', ' '.join(cmd), error.decode('utf-8').strip()]))  # just display errors in the console windows
            return

        # if write to file, open
        # if oformat is not None and oformat in get_user_settings('pandoc-format-file'):
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


def get_user_settings(window, working_dir=None, file_name=None):
    '''Return the default settings merged with the user's settings.'''


    # returns the currently edited view.
    view = window.active_view()

    # configLoc = walkIncludes("pandoc-config.json", working_dir, window)

    settings = sublime.load_settings('Pandoc.sublime-settings')
    default = settings.get('default', {})
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

    return default



def walkIncludes(lookFor, working_dir, window=None, prepend=None):
    '''
    Check the includes_paths, then the project hierarchy, for the file to include,
    but only if we don't already have a path.
    Order of preference should be: working DIR, project DIRs, then includes_paths,
    then finally giving up and passing the filename to Pandoc.
    '''

    debug("Looking for " + lookFor)
    # Did the user pass a specific file?
    tryAbs = os.path.abspath(os.path.expanduser(lookFor))
    if os.path.isfile(tryAbs):
        debug("It's a path! Returning.")
        return prepend + tryAbs if prepend else tryAbs

    # Is the file in the current build directory?
    tryWorking = os.path.join(working_dir, lookFor)
    if os.path.exists(tryWorking):
        debug("It's in the build directory! Returning.")
        return prepend + tryWorking if prepend else tryWorking

    # Is the file anywhere in the project hierarchy?
    # if window
    allFolders = window.folders()
    debug("allFolders: " + str(allFolders))
    if len(allFolders) > 0:
        topLevel = ""
        (garbage, localName) = os.path.split(working_dir)
        for folder in allFolders:
            for root, dirs, files in os.walk(folder, topdown=False):
                (garbage, rootTail) = os.path.split(root)
                if rootTail == localName:
                    topLevel = root
                for name in dirs:
                    debug("name: " + name)
                    if name == localName:
                        topLevel = folder
        debug("topLevel: " + topLevel)
        checkDIR = working_dir
        debug("Initial checkDIR: " + checkDIR)
        if topLevel:
            while True:
                fileToCheck = os.path.join(checkDIR, lookFor)
                if os.path.exists(fileToCheck):
                    debug("It's in the project! Returning %s." % fileToCheck)
                    return prepend + fileToCheck if prepend else fileToCheck
                if checkDIR == topLevel:
                    break
                else:
                    checkDIR = os.path.abspath(os.path.join(checkDIR, os.path.pardir))

    # Are there no paths to check?
    if self.includes_paths_len == 0 and lookFor != "pandoc-config.json":
        debug("No includes paths to check. Returning the input for Pandoc to handle.")
        return prepend + lookFor if prepend else lookFor
    # Is the file in the includes_paths?
    for pathToCheck in self.includes_paths:
        pathToCheck = os.path.expanduser(pathToCheck)
        pathToCheck = os.path.abspath(pathToCheck)
        fileToCheck = os.path.join(pathToCheck, lookFor)
        if os.path.isfile(fileToCheck):
            debug("It's in the includes paths! Returning: " + fileToCheck)
            return prepend + fileToCheck if prepend else fileToCheck

    # If the script was checking for a pandoc-config.json, return None.
    if lookFor == "pandoc-config.json":
        debug("Couldn't find config file in project path.")
        return None
    else:
        # The file wasn't anywhere, so let Pandoc handle it.
        debug("Can't find %s. Letting Pandoc deal with it." % lookFor)
        return prepend + lookFor if prepend else lookFor

    sublime.error_message("Fatal error looking for {0}".format(lookFor))
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
