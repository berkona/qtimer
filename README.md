# qTimer #

A small command line extendable timer that integrates with various project
management solutions.

## Installation and Configuration ##

qTimer can be installed via the 
[Python Package Index](http://pypi.python.org/pypi/qTimer) or via setup.py.  
qTimer depends upon [SQLAlchemy](http://pypi.python.org/pypi/SQLAlchemy) 
and [Alembic](http://pypi.python.org/pypi/alembic) to run.

After installing you have to copy the site-packages/qtimer/default.ini to
$HOME/.qtimer. You can also configure things such as how long will qTimer 
cache data from remote sources and how much will
it round time in both display and posting.  The `[alembic]` and `[loggers]`
sections are for advanced users only, and the average user should probably
steer clear of those.

## Posting with a Plugin ##

By default qTimer runs with the `offline` plugin, which doesn't not allow 
syncing with a remote project management server.  qTimer can be extended 
with many different plugins that let you post time records. By default qTimer
has the following plugins:

### Freshbooks ###

`Requires the [refreshbooks](https://pypi.python.org/pypi/refreshbooks/) python module.`

```
[account]
type = freshbooks
url = accountname.freshbooks.com
token = XXXXXXXXXXXXXXXXXXXXXXXX
```

### Active Collab ###

`Currently broken pending pycollab updating for Python3/ActiveCollab3`

```
[account]
type = activecollab
url = ac.acmecorp.com
token = 194-XXXXXXXXXXXXXXXXXXXX
```

## Extending qTimer ##

If you're interested in extending qTimer take a look at the plugins folder
and the commands folder.

A command is a class which provides a sub-parser and business logic
for a given sub-command. See commands folder and command.py for details

A plugin represents a way of retrieving data from a remote source.  Plugins
are required to have the magic method load_qtimer_plugin(url, token).  See
plugins/plugin.prototype.py for more details.
