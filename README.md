# __Spandoc__ — Pandoc inside Sublime

A [Sublime Text](https://www.sublimetext.com/) plugin that uses the infamous open-source parser [Pandoc](http://pandoc.org/) to convert text in nearly every possible format into each other.
With Pandoc you can use the most evolved Markdown implementation: [Pandoc's Markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) and with __Spandoc__ you can use it inside Sublime Text!

__Spandoc__ is composed of [Brian Fisher](https://github.com/tbfisher)'s plugin [„pandoc“](https://packagecontrol.io/packages/Pandoc) and of [Daniel P. Shannon](https://github.com/phyllisstein)'s plugin [Pandown](https://packagecontrol.io/packages/Pandown). __Spandoc__ came into existance to combine the strengths of these two plugins. Starting from the light code base by „pandoc“ and its command palette, a build-system was added to it and it was made async in execution. The configuration system by Pandown was incorporated and the code base was cleared and refactored even more. Other functions from Pandown will follow and be transferred to __Spandoc__.

## License

MIT License, see `LICENSE.md`



## Installation

- [Install Pandoc](http://pandoc.org/installing.html)
- Install __Spandoc__ by either use:
  + [Package Control](https://packagecontrol.io/): Run the command: `Package Control: Install Package` and find `Spandoc`.
  + Github: clone or download the [Spandoc repository](https://github.com/geniusupgrader/Spandoc) into your Sublime (loose) packages directory (use the menu `Preferences->Browse Packages…` to find this folder)


## Usage

__Spandoc__ needs to know the command options for Pandoc. At least an input and an output format.

- The input format is automatically taken from the scope under the cursor of the current document, when executing the [commands](#commands).
- The output format must be configured in a settings file by defining the `transformations` array, see the [Configuring](#configuring) section.

Start a Pandoc conversion:

1. You can bring up the Sublime Command Palette (default shortcut: `ctrl+shift+p`) and execute the `Spandoc` command. You will be presented with a list of transformations. After choosing a transformation label from the transformation list, the Pandoc conversion will begin. The list can be configured.
2. You can use Sublime's automatic build system (`Tools -> Build System -> Automatic`). The Pandoc conversion will begin when executing it (default shortcut: `ctrl+b`). This is only pre-configured for Markdown to HTML and Markdown to PDF.
3. You can use the internal `spandoc_run` command in your user keybindings file. This must be configured, see [Keybindings](#keybindings).


## Commands

There are three commands: `Spandoc Palette` and `Spandoc: Create Config` and the internal `spandoc_run` command.

### Spandoc Palette

The `Spandoc` command opens a command palette and lists the defined transformations from a settings file (in dependence of the scope under the cursor). Afer choosing one transformation label, the transformation will be passed to the internal `spandoc_run` command and the Pandoc conversion will begin.


### Spandoc: Create Config

This command creates the *Current folder settings file*. If available, it will copy the *user settings file*, otherwise the *default settings file* to the current folder (with the current document).


### spandoc_run

The `spandoc_run` command gets the settings, forms the pandoc command, passes the pandoc command to Pandoc, catches/shows the results and failures and either write it to a file or displays it in Sublimes buffer.



## Settings structure

- _Default settings file_ `spandoc.sublime-settings`, located inside the package directory of Sublime
- _User settings file_ (with the same name), located inside the user directory of Sublime.
- _Current folder settings file_ `spandoc.json`, located inside the current folder (or subfolders).

Listed in reverse precedence: Folder settings overwrite User settings overwrite default settings.

- _Default build system file_ `Spandoc.sublime-build`, located inside the package directory of Sublime
- _User build system file_ (with the same name) `Spandoc.sublime-build`, located inside the user directory of Sublime



## Configuring

It is advised not to alter the *default settings file*, because on every new update it gets overwritten. Copy the *default settings file* to the *user settings file*. Both can be found via the application menu: `Preferences -> Package Settings -> Spandoc`.

There are 2 possible top level setting keys, `user` and `default`. If you use `default` in your *user settings file*, the default settings will be overwritten, but if you use `user` your settings will be merged into the default settings.

In the settings, you need to configure the path to the Pandoc executable. This can be done with the `pandoc-path` parameter. See the *default settings file* for default locations.

With the `transformations` array, you can define several different transformations. Every transformation needs at least:

- transformation label/name
- `pandoc-arguments` array with...
	+ the `--from` argument
	+ and the `--to` argument

The transformation label is only a Name for the transformation. This name is for example displayed in the command palette and will be always used to choose the transformation. The `--from` and `--to` arguments, plus any additional argument inside the `pandoc-arguments` array, must follow Pandocs [naming rules](http://pandoc.org/MANUAL.html#options). Propably the `--from` argument should have a similar name as the transformation label.

For the pandoc commands the short version as well as the long version can be used. For example, the short version:  `"-o name_of_file"` or the long version: `"--output=name_of_file"`. Although the long version is preferred in this Sublime Plugin.

Like native Pandoc the conversion result goes to `stdout` by default. In __Spandoc__ and Sublime this means that it is written to the buffer (Buffer not yet implemented, it always writes to a file).

The extension is taken from the corresponding output format, specified with the `--to` option. Howewer, the file extension can be specified with the `output_extension` parameter _outside_ the `pandoc-arguments` array. This is especially useful, where the `--to` option does not correspond with the extension, like in the case of reveal.js, where in Pandoc the command `--to=revealjs` must be given.


For outputting to a file, use the `-output` option.
When outputting to a file, the file will be written to the same folder as the input file, unless otherwise specified with the optional `set_path` option (`set_path` not yet implemented!). The output file will have the same name as the input file, unless otherwise specified with the `--output` option.






Look in the [Pandoc User's Guide](http://pandoc.org/MANUAL.html). __Every other possible Pandoc option can be used__ inside `pandoc-arguments`.



### Sublime build system

The automatic build system of Sublime (`ctrl+b`) will pass the transformation label from the build system file straight to the internal `Spandoc_run` command and the Pandoc conversion will begin.

After configuring the `transformation` argument in the build system file.




## Keybindings

No default keyboard shortcuts are predetermined, but you can easily configure them by using the internal command names:

```json
{
  "keys": ["ctrl+e"],
  "command": "spandoc_palette"
},
```

You can even execute the internal command: `spandoc_run` with a keybinding, passing the transformation parameter directly:

```json
{
  "keys": ["ctrl+e"],
  "command": "spandoc_run",
  "args": {"transformation": "HTML"}
},
```


## Contributing

TODO

No Sublime 2 support.

