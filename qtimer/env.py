from appdirs import AppDirs
from os import path

APP_NAME = 'qTimer'
ORG_NAME = 'Solipsis Development'
INI_NAME = '.qtimer'
LOG_NAME = 'debug.log'

VERSION = '0.1.4'

PLUGIN_MOD = 'qtimer.plugins.%s'
COMMANDS_MOD = 'qtimer.commands.%s'

APP_DIRS = AppDirs(APP_NAME, ORG_NAME, roaming=True)

SCRIPT_ROOT = path.dirname(path.realpath(__file__))

DATA_DIR = APP_DIRS.user_data_dir

CONFIG_PATH = path.expanduser(path.join('~', INI_NAME))
LOG_PATH = path.join(APP_DIRS.user_log_dir, LOG_NAME)
