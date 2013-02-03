qTimer
-------

A small command line extendable timer that integrates with various project
management solutions.

Installation and Configuration
===============================

qTimer can be install via the
[Python Package Index](http://pypi.python.org/pypi/qTimer) or via
setup.py.  qTimer depends upon
[SQLAlchemy](http://pypi.python.org/pypi/SQLAlchemy) and
[Alembic](http://pypi.python.org/pypi/alembic) to run.

You should take the time to configure qTimer before running it for the first
time.  Basic configuration is to copy the dist-packages/qtimer/default.ini to
$HOME/.qtimer and then change the url and token.  You can also configure things
such as how long will qTimer cache data from remote sources and how much will
it round time in both display and posting.  The `[alembic]` and `[loggers]`
sections are for advanced users only, and the average user should probably
steer clear of those.


Extending qTimer
=================

If you're interested in extending qTimer take a look at the plugins folder
and the commands folder.

A command is a class which provides a sub-parser and business logic
for a given sub-command. See commands folder and command.py for details

A plugin represents a way of retrieving data from a remote source.  Plugins
are required to have the magic method load_qtimer_plugin(url, token).  See
plugins/plugin.prototype.py for more details.
