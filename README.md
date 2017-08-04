# _Spandoc_ — Pandoc inside Sublime

A [Sublime Text](https://www.sublimetext.com/) plugin that uses the infamous open-source parser [Pandoc](http://pandoc.org/) to convert text in nearly every possible format into each other.
With Pandoc you can use the most evolved Markdown implementation: [Pandoc's Markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) and with _Spandoc_ you can use it inside Sublime Text!

_Spandoc_ is composed of [Brian Fisher](https://github.com/tbfisher)'s plugin [„pandoc“](https://packagecontrol.io/packages/Pandoc) and of [Daniel P. Shannon](https://github.com/phyllisstein)'s plugin [Pandown](https://packagecontrol.io/packages/Pandown). _Spandoc_ came into existance to combine the strengths of these two plugins. Starting from the light code base by „pandoc“ and its command palette, a build-system was added to it and it was made async in execution. The configuration system by Pandown was incorporated and the code base was cleared and refactored even more. Other functions from Pandown will follow and be transferred to _Spandoc_.


## Installation

- [Install Pandoc](http://pandoc.org/installing.html)
- Install Spandoc by either use:
  + [Package Control](https://packagecontrol.io/): Run the command: `Package Control: Install Package` and find `Spandoc`.
  + Github: clone or download the [Spandoc repository](https://github.com/geniusupgrader/Spandoc) into your Sublime (loose) packages directory (use the menu `Preferences->Browse Packages…` to find this folder)


## Usage

_Spandoc_ needs to know the command options for Pandoc. At least an input and an output format.

- The input format is automatically taken from the scope under the cursor of the currently edited document, when executing the [commands](#commands).
- The output format is called a transformation in _Spandoc_. It must be configured in a settings file by defining the `transformations` array.

Two ways to start a Pandoc conversion:

1. After configuring the transformations (see [Configuring](#configuring)) you can bring up the Sublime Command Palette (`ctrl+shift+p`) and execute the `Spandoc` command. Then you can choose a transformation label from the transformation list and the Pandoc conversion will begin.
2. After configuring the `transformation` argument in a build system file, you can use Sublime's automatic build system (`Tools -> Build System -> Automatic`). The Pandoc conversion will begin when executing it (`ctrl+b`).

## Commands

There are two commands: `Spandoc` and `Spandoc: Create Config` and the Sublime build system.

#### `Spandoc`
Internal command name: `spandoc_palette`

The `Spandoc` command opens a command palette and lists the defined transformations from a settings file (in dependence of the scope under the cursor). Afer choosing one transformation label, the transformation will be passed to the internal `spandoc_run` command and the Pandoc conversion will begin.


#### `Spandoc: Create Config`
Internal command name: `spandoc_create_config`

This command creates the `folder settings file`. It will copy either the `user settings file` or the `default settings file` to the folder within the currently edited document.


### Sublime build system

The automatic build system of Sublime (`ctrl+b`) will pass the transformation label from the build system file straight to the internal `Spandoc_run` command and the Pandoc conversion will begin.


## Settings structure

- _Default settings file_ `spandoc.sublime-settings`, located inside the package directory of Sublime
- _User settings file_ (with the same name), located inside the user directory of Sublime.
- _Folder settings file_ `spandoc.json`, located inside the folder or subfolders within the currently edited document.

Listed in reverse precedence: Folder settings overwrite User settings overwrite default settings.

- _Default build system file_ `Spandoc.sublime-build`, located inside the package directory of Sublime
- _User build system file_ (with the same name) `Spandoc.sublime-build`, located inside the user directory of Sublime



## Configuring

It is advised not to alter the `default settings file`, because on every new update it'll get overwritten. Copy the `default settings file` to the `user settings file`. Both can be found via the application menu, go to `Preferences -> Package Settings -> Spandoc`.

In the `user settings file` you need to configure the path to the Pandoc executable. This can be done with the `pandoc-path` parameter. See the `default settings file` for default locations. 

There are 2 possible top level settings keys, `user` and `default`. If you use `default` in your `user settings file`, the default settings will be overwritten, but if you use `user` your settings will be merged into the default settings.

With the `transformations` you define an output format for Pandoc. Every transformation needs at least:

- transformation label
- `scope` array
- `pandoc-arguments` array with the `--to` parameter at minimum

The transformation label is only a Name for the transformation. This name is for example displayed in the command palette and will be always used to choose the transformation. The `scope` array decides if the transformation can be applied (it is in fact a `--from` parameter). Maybe it is more reasonable to just take the syntax of the currently edited file and not the scope under the cursor… The `--to` parameter, which must be inside the `pandoc-arguments` array is the `--to` parameter for Pandoc. Because of that it must follow the [naming rules](http://pandoc.org/MANUAL.html#options) by Pandoc, but propably it should have a similar name as the transformation label.

__Every other possible Pandoc option can be used__ inside `pandoc-arguments`, look in the [Pandoc User's Guide](http://pandoc.org/MANUAL.html). 

## Keyboard shortcuts

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

