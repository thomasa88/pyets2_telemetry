# pyets2_telemetry

*Python plug-in support for SCS Telemetry SDK*

## Introduction

pyets2_telemetry provides support for adding Python plug-ins to ETS2 ([Euro Truck Simulator 2](https://eurotrucksimulator2.com/)) by SCS Software. It consists of two parts: A native C++ ETS2 plug-in, that the game loads, and a Python framework, which is loaded by the native plug-in. The Python framework provides a plug-in API that is very similar to the ETS2 native API.

## Installation

> **NOTE**
>
> This plug-in provides support for plug-ins written in the [Python](https://www.python.org/) programming language. By itself, it does not provide any gaming functionalities. So after installing it, add a Python plug-in.
>
> E.g. [pyets2_telemetry_server](https://github.com/thomasa88/pyets2_telemetry_server) provides a telemetry server, compatible with [ETS2 Telemetry Web Server](https://github.com/Funbit/ets2-telemetry-server).

Download the latest release archive (`.tar.bz2`) from the [release page](https://github.com/thomasa88/pyets2_telemetry/releases) and unpack it in the ETS2 `plugins` directory (typically `"$HOME/.steam/steam/steamapps/common/Euro Truck Simulator 2/bin/linux_x64/plugins"`).

You can find the *plugins* directory in Steam, by right-clicking the game and selecting *Properties...* -> *LOCAL FILES* -> *BROWSE LOCAL FILES...* and then open the directories `bin/linux_64/plugins`. 

The unpacked file structure should look similar to this:

```
Euro Truck Simulator 2
└── bin
    └── linux_x64
        └── plugins
            ├── pyets2_telemetry_loader_1_0.so
            └── python
                └── pyets2lib
```

When you start the game, if the plug-in is detected, it will show a dialog about *Request to use advanced SDK features detected.*

## Compatibility

pyets2_telemetry has been tested with Euro Truck Simulator 2 version 1.35 on Ubuntu 18.04, with Python 3.6.

## Performance

Observations have not showed any visible decrease in FPS.

## Development

### Writing a Plug-in

For now, there are no example plug-ins. Refer to [pyets2_telemetry_server](https://github.com/thomasa88/pyets2_telemetry_server) for a (complex) example.

The Python API tries to mirror the SCS API. Refer to the documentation in the [Telemetry SDK](https://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry) for a description of the SCS API functionality and call flow, including descriptions of *channels* and *events*.

It is important that your plug-in handles being unloaded and reloaded.

#### API Functions

In essence, the following functions are used:

* `telemetry_init(version, params)` Called when the plug-in is loaded by ETS2
  * `params`members include:
    * `register_for_channel(channel, channel_cb, index, context)`
    * `register_for_event(event, event_cb, context)`
    * `common.logger` Provides a Python `logger` for the plug-in, which logs to the in-game console.
* `telemetry_shutdown()`Called when the plug-in is being unloaded. Make sure to stop any threads that you have started.

Notably, the following functions are currently missing, but should not be needed in most cases:

* `unregister_from_channel()`
* `unregister_from_event()`

Examine `python/pyets2lib/loader.py`, and possibly `loader.cpp`, for more information.

#### Constants and Helpers

* `pyets2lib.scsdefs` Provides definitions for channels and events.

* `pyets2lib.scshelpers` Contains helper functions.

#### Useful ETS2 Commands and Settings

##### Game Configuration

`"$HOME/.local/share/Euro Truck Simulator 2/config.cfg"`

* `uset g_developer "1"` Enable developer mode
* `uset g_console "1"` Enable in-game console
* `uset g_minicon "1"` Enable in-game mini console
* `uset g_fps "1"` Show FPS in mini console

##### Console Commands

* `sdk reload` Reload all plug-ins
* `sdk unload` Unload all plug-ins

##### Controls Configuration

If the console hotkey (`` ` ``) is not working, it can be remapped to another key by changing the controls configuration. To find out the name for the wanted key, assign it to a function in the game settings and inspect the resulting configuration.

`"$HOME/.local/share/Euro Truck Simulator 2/*profiles/*/controls_linux.sii"`

```
 "mix console `modifier(no_modifier, keyboard.grave?0)`"
```
### Loader Development

The loader is made up of two parts: The C++ native loader and the Python framework.

#### Native Loader

The native loader uses the [Python/C API](https://docs.python.org/3/c-api/) to load the Python framework. Source code is found in the `cpp` and `hpp` files. `loader.cpp` is the starting point.

Build the code using `make`. The `Makefile` expects to find `eurotrucks2_telemetry_sdk_1.10` in the top source directory.

The output library is called `pyets2_telemetry_loader.so`.

`test.cpp` is a very rudimentary test application, that loads the loader and makes some function calls into it. Build the `test` binary using `make test`.

#### Python Framework

Source code is found in the `python` directory. `loader.py` is the starting point.

#### Installation and Packaging

The following `make` targets handles installation and packaging:

* `install` Install pyets2_telemetry into the plugins directory.
* `install-dev` Install symlinks to pyets2_telemetry files into the plugins directory.
* `uninstall` Remove pyets2_telemetry files from the plugins directory.
* `package` Package pyets2_telemetry into `pyets2_telemetry_<VERSION>.tar.bz2` for distribution.

 All targets related to installation requires a `DESTDIR` variable, pointing to the ETS2 plugins directory. For example:

 ```
make DESTDIR="$HOME/.steam/steam/steamapps/common/Euro Truck Simulator 2/bin/linux_x64/plugins" install
 ```


## Future Improvements

The following points need improvement:

* Handling Python [daemon threads](https://docs.python.org/3/library/threading.html). Currently, the game sporadically crashes when unloading plug-ins with daemon threads.
* Kill left-over Python threads. A Python plug-in can hang the game when being unloaded (game exit, `sdk unload`) by not stopping all its threads.
* Support for unregistering from channels and events.
* Handle the user trying to use two copies of the library at the same time.
* Windows support.

## License

pyets2_telemetry is licensed under GPL 3.0. Refer to the file [LICENSE][LICENSE].

## SCS SDK License

pyets2_telemetry uses the *SCS Telemetry SDK*, which has the following license:

> SCS SDK
> Copyright (C) 2016 SCS Software
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.