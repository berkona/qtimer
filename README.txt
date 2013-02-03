qTimer
======

A small command line extendable timer that integrates with various project
management solutions.

Extending qTimer
=================

If you're interested in extending qTimer take a look at the plugins folder
and the commands folder.

A command is a class which provides a sub-parser and business logic
for a given sub-command. See commands folder and command.py for details

A plugin represents a way of retrieving data from a remote source.  Plugins
are required to have the magic method load_qtimer_plugin(url, token).  See
plugins/plugin.prototype.py for more details.
