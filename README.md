# __Spandoc__ — Pandoc inside Sublime

A [Sublime Text](https://www.sublimetext.com/) plugin that uses the infamous open-source parser [Pandoc](http://pandoc.org/) to convert text in nearly every possible format into each other.
With Pandoc you can use the most evolved Markdown implementation: [Pandoc's Markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) and with __Spandoc__ you can use it inside Sublime Text!

__Spandoc__ is composed of [Brian Fisher](https://github.com/tbfisher)'s plugin [„pandoc“](https://packagecontrol.io/packages/Pandoc) and of [Daniel P. Shannon](https://github.com/phyllisstein)'s plugin [Pandown](https://packagecontrol.io/packages/Pandown). __Spandoc__ came into existance to combine the strengths of these two plugins. Starting from the light code base by „pandoc“ and its command palette functionality, taking the "project" configuration system by Pandown and adding entirely new features. The code base is heavily cleared and refactored. This plugin is in development and of course __Spandoc__ is used by myself.




## License

MIT License, see [`LICENSE.md`](https://github.com/geniusupgrader/Spandoc/blob/master/LICENSE.md)


## Installation

- [Install Pandoc](http://pandoc.org/installing.html)
- Install __Spandoc__ by either:
  + [Package Control](https://packagecontrol.io/packages/Spandoc): Run the command: `Package Control: Install Package` and find `Spandoc`.
  + or Github: clone or download the [Spandoc repository](https://github.com/geniusupgrader/Spandoc) into your Sublime (loose) packages directory (use the menu `Preferences->Browse Packages…` to find this folder)



## Commands

There are three commands: `Spandoc Palette` and `Spandoc: Config` and the internal `spandoc_run` command.


### Spandoc: Palette

Bring up the Sublime Command Palette (default shortcut: `ctrl+shift+p`) and execute the `Spandoc: Palette` command. In dependence of the scope under the cursor, a list of defined transformations from a settings file will be persented. After choosing one label from from the transformation list, the transformation label will be passed to the internal `spandoc_run` command and the Pandoc conversion will begin. The list can be configured, see the [Configuring](#configuring) section.


### Spandoc: Config

This command creates a current folder settings file (called `spandoc.json`), by copying it either from the user settings file or from the default settings file. After creating, it will open immediately. When there is already a `spandoc.json` file, it does _not_ overwrite it, only opens it.


### spandoc_run

The `spandoc_run` is the core of __Spandoc__: it gets the settings, forms the pandoc command, passes the pandoc command to Pandoc, catches/shows the results and failures and either write it to a file or displays it in Sublimes buffer (buffer not yet implemented).


## Settings structure


Listed in the order of loading.

- Default settings file `spandoc.sublime-settings`, located inside the package directory of Sublime inside the __Spandoc__ folder
- User settings file `spandoc.sublime-settings`, located inside the user directory of Sublime.
- Folder settings file `spandoc.json`, located inside the current folder (optional)
- User build system file `Spandoc.sublime-build`, located inside the user directory of Sublime (optional)

Settings at the bottom of this list take precedence over the entries above. Folder settings overwrite User settings overwrite default settings.


## Configuring

It is advised not to alter the default settings file, because on every new update it gets overwritten. Copy the default settings file to the user settings file. Both can be found via the application menu: `Preferences -> Package Settings -> Spandoc`.

There are 2 possible top level setting keys, `user` and `default`. If you use `default` in your user settings file, the default settings will be overwritten, but if you use `user` your settings will be merged into the default settings. (This functionality will be removed)

In the settings, you need to configure the path to the Pandoc executable. This can be done with the `pandoc-path` parameter. See the default settings file for default locations.

__Spandoc__ needs to know the command options for Pandoc. At least an input and an output format.

- The input format is automatically taken from the scope under the cursor of the current document.
- The output format must be configured in a settings file by defining the `transformations` array. With the `transformations` array, you can define several different transformations. Every transformation needs at least:

- transformation label/name
- `pandoc-arguments` array with...
  + the `--to` argument

The transformation label is only a Name for the transformation. This name is for example displayed in the command palette and will be always used to choose the transformation. The `--to` argument, plus any additional argument inside the `pandoc-arguments` array, must follow Pandocs [naming rules](http://pandoc.org/MANUAL.html#options).

For the pandoc commands the short version as well as the long version can be used. For example, the short version:  `"-o name_of_file"` or the long version: `"--output=name_of_file"`. Although the long version is preferred in this Sublime Plugin.

Like native Pandoc the conversion result goes to `stdout` by default. In __Spandoc__ and Sublime this means that it is written to the buffer (Buffer not yet implemented, it always writes to a file).

The extension is taken from the corresponding output format, specified with the `--to` option. Howewer, the file extension can be specified with the `output_extension` parameter _outside_ the `pandoc-arguments` array. This is especially useful, where the `--to` option does not correspond with the extension. Two examples:

1. For PDF you must specify: `--to=latex` and `output_extension=pdf`
2. For reveal.js: `--to=revealjs` and `output_extension=html`

For outputting to a file, use the `--output` option, otherwise it will be written to buffer (buffer not yet implemented, it will always write a file, `--output` is always automatically set).
When outputting to a file, the file will be written to the same folder as the input file, unless otherwise specified with the optional `set_path` option (`set_path` not yet implemented!). The output file will have the same name as the input file, unless otherwise specified with the `--output` option.

Look in the [Pandoc User's Guide](http://pandoc.org/MANUAL.html). __Every other possible Pandoc option can be used__ inside `pandoc-arguments`.

Please pay attention on the format of the `spandoc.sublime-settings` file. It should be valid `json`. And when the commands contain spaces, the best method is to encapsulate them in escaped quotation marks, like this:




### Spandoc build system

Uses Sublime's automatic build system (`Tools -> Build System -> Automatic`) to execute the internal `spandoc_run` command.

There is no default build configuration, because of three reasons:

1. Not every person is using this functionality
2. Together with a user build configuration it will pollute the sublime palette (like [Pandown](https://packagecontrol.io/packages/Pandown) is doing it)
3. The build system can be easily configured

For configuring the build system with Spandoc, the easiest solution is to copy the following template into the user build settings, located in the menu at `Preferences -> Package Settings -> Spandoc -> Build user settings`:

```json
{

  "selector": "text.html.markdown",
  "target": "spandoc_run",
  "transformation": "HTML",

  "variants":
    [
      { "name": "PDF", "transformation": "PDF" },
      { "name": "HTML", "transformation": "HTML (No Template)" },
    ]

}
```

After configuring the `transformation` argument in the build system file, the automatic build system of Sublime (`ctrl+b`) will pass the transformation label from the build system file straight to the internal `Spandoc_run` command and the Pandoc conversion will begin.



### Keybindings


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

Contributing notes will follow.
Code of Conduct will follow.
No Sublime 2 support

