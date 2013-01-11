from appdirs import AppDirs
from os import path

import sqlalchemy.engine.url as url
from qtimer.config import Config

PLUGIN_MOD = 'qtimer.plugins.%s.plugin'
COMMANDS_MOD = 'qtimer.commands.%s'

APP_NAME = 'qTimer'
ORG_NAME = 'Solipsis Development'
INI_NAME = 'qtimer.ini'
DEFAULT_NAME = 'default.ini'

APP_DIRS = AppDirs(APP_NAME, ORG_NAME, roaming=True)

SCRIPT_ROOT = path.dirname(path.realpath(__file__))
DEFAULT_CONFIG_PATH = path.join(SCRIPT_ROOT, DEFAULT_NAME)
DATA_DIR = APP_DIRS.user_data_dir
CONFIG_PATH = path.join(DATA_DIR, INI_NAME)

__DB_COMPAT_TABLE__ = {
	'sqlite': {
		'passive_updates': False,
		'emit_pragma_fk': True
	},
}

__DEFAULT_DB_COMPAT_TABLE__ = {
	'passive_updates': True,
	'emit_pragma_fk': False
}


def getDatabaseCompatability():
	config = Config(CONFIG_PATH, DEFAULT_CONFIG_PATH)
	dbUrl = url.make_url(config.alembic.sqlalchemy_url)
	dialect = dbUrl.get_dialect()
	return __DB_COMPAT_TABLE__.get(dialect, __DEFAULT_DB_COMPAT_TABLE__)

def allowsCascading():
	return getDatabaseCompatability()['passive_updates']
