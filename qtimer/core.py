# System imports
from datetime import datetime, timedelta
from os import path, listdir
from contextlib import contextmanager
from importlib import import_module


import argparse
import logging

import logging.config
import logging.handlers

# SQLALchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlalchemy as sa
import alembic.command

# Custom
from qtimer.util import smart_truncate, autocommit, expand_sql_url
from qtimer.model import Ticket, Project, PersistentVar
from qtimer.lib import terminalsize
from qtimer.strings import strings
from qtimer.config import Config
from qtimer.env import *


# This is what we use for writing to the database
SQLSession = sa.orm.sessionmaker()

CoreLogger = logging.getLogger(__name__)


class QTimerCore(object):

	def __init__(self, configPath, defaultsPath):
		self.configPath = configPath
		self.defaultsPath = defaultsPath

	# We use getter properties to offset resource creation until we need it
	@property
	def commands(self):
		if hasattr(self, '_commands'):
			return self._commands

		self._commands = {}
		commandPath = path.join(SCRIPT_ROOT, 'commands')

		files = (path.splitext(item)[0] for item in listdir(commandPath)
			if (not (item == '__init__.py' or item == 'command.py'))
				and path.isfile(path.join(commandPath, item)))

		for f in files:
			self.importCommand(f)

		return self._commands

	@property
	def lastSynced(self):
		if hasattr(self, '_lastSynced'):
			return self._lastSynced
		q = self.session.query(PersistentVar)\
			.filter(PersistentVar.name.like('internal.lastSynced'))
		try:
			self._lastSynced = q.one().value
			# CoreLogger.debug('lastSynced: %s, now: %s, delta: %s', self._lastSynced, datetime.utcnow(), datetime.utcnow() - self._lastSynced)
			return self._lastSynced
		except BaseException as e:
			CoreLogger.warn('Encountered exception: %s', repr(e))
			pass

	@property
	def session(self):
		if hasattr(self, '_session'):
			return self._session

		# This also has the side-effect of initializing the database and logging
		alembic.command.upgrade(self.config, "head")

		self.engine = sa.create_engine(
			expand_sql_url(self.config.alembic.sqlalchemy_url),
			encoding="utf-8", echo=False
		)

		SQLSession.configure(bind=self.engine)

		self._session = SQLSession()
		return self._session

	@property
	def plugin(self):
		if hasattr(self, '_plugin'):
			return self._plugin

		url = self.config.account.url
		token = self.config.account.token
		accountType = self.config.account.type
		if not (url and token and accountType):
			raise RuntimeError(strings['bad_config'])

		try:
			mod = import_module(PLUGIN_MOD % accountType)
			self._plugin = mod.load_qtimer_plugin(url, token)
			return self._plugin
		except ImportError:
			raise RuntimeError(strings['no_plugin_found'] % accountType)

	@property
	def parser(self):
		if hasattr(self, '_parser'):
			return self._parser

		parser = argparse.ArgumentParser()

		subparsers = parser.add_subparsers(title=strings['command_title'], dest='op')

		for identifier, command in self.commands.items():
			if hasattr(command, 'COMMAND_HELP'):
				subparser = subparsers.add_parser(identifier, help=command.COMMAND_HELP)
			else:
				subparser = subparsers.add_parser(identifier)
			command.addArguments(subparser)

		self._parser = parser
		return self._parser

	@property
	def config(self):
		if hasattr(self, '_config'):
			return self._config

		self._config = Config(self.configPath, self.defaultsPath)
		return self._config

	def parseArgs(self, argsOverride=None):
		args = self.parser.parse_args(argsOverride)
		if not args.op:
			self.parser.print_help()
			raise RuntimeError(strings['no_op'])

		return vars(args)

	def importCommand(self, f):
		# Predict the class name to be the TitleCase of the script mod
		className = f.title().replace('_', '')
		mod = import_module(COMMANDS_MOD % f)
		command = getattr(mod, className)()

		if not hasattr(command, 'COMMAND_IDENTIFIER'):
			raise RuntimeError('Command %s must declare an ID' % (COMMANDS_MOD % f))

		self._commands[command.COMMAND_IDENTIFIER] = command

	def executeCommand(self, args):
		command = self.commands.get(args['op'], None)
		if not command:
			raise RuntimeError('No command found matching ' + args['op'])
		return command.runCommand(args, self)

	def outputRows(self, rows=[], header=(), weights=()):
		logger = logging.getLogger('output')
		if not weights:
			lenHeader = len(header)
			weights = tuple([(1 / lenHeader) for i in range(lenHeader)])

		totalWeight = sum(weights)
		if (totalWeight > 1 or totalWeight < 0.99):
			raise RuntimeError('The sum of all weights must be about 1, totalWeight: %f' % totalWeight)

		totalWidth = terminalsize.get_terminal_size()[0]
		widths = []
		formatStr = ''
		for weight in weights:
			width = int(totalWidth * weight)
			formatStr += '%-' + str(width) + 's'
			widths.append(width)

		logger.info(formatStr % header)
		logger.info('-' * totalWidth)
		for row in rows:
			items = []
			for i, item in enumerate(row):
				if isinstance(item, str) and len(item) > widths[i]:
					item = smart_truncate(item, widths[i])
				items.append(item)
			logger.info(formatStr % tuple(items))

	def syncConditionally(self):
		mins = int(self.config.account.cache_lifetime)
		lifetime = timedelta(minutes=mins)

		if (not self.lastSynced or (datetime.utcnow() - self.lastSynced) > lifetime):
			self.sync()

	def sync(self):
		CoreLogger.info(strings['old_data'],
			self.config.account.type, self.config.account.url)

		with autocommit(self.session) as session:
			project_ids = []
			ticket_ids = []

			session.query(Project).delete()
			session.query(Ticket).delete()

			projects = self.plugin.listProjects()
			for project in projects:
				project_ids.append(project.id)
				session.add(project)
				tickets = self.plugin.listTickets(project.id)
				for ticket in tickets:
					ticket_ids.append(ticket.id)
					session.add(ticket)

			lastSynced = PersistentVar(name='internal.lastSynced', value=datetime.utcnow())
			session.merge(lastSynced)

	def roundTime(self, dt):
		roundTo = int(self.config.timers.rounding)
		seconds = (dt - dt.min).seconds
		# // is a floor division not a comment on the following line
		rounding = (seconds + roundTo / 2) // roundTo * roundTo
		ms = dt.microseconds if hasattr(dt, 'microseconds') else 0
		ret = dt + timedelta(0, rounding - seconds, -ms)
		return ret

	def close(self):
		CoreLogger.info('QTimerCore shutdown.')
		CoreLogger.info('Flushing and closing all retained sessions')

		# If we call self.session, we will initialize the db, which would be bad
		# If we haven't already
		if (hasattr(self, '_session')):
			self.session.flush()
			self.session.close()


@event.listen_for(Engine, 'connect')
def set_sqlite_pragma(conn, conn_record):
	cursor = conn.cursor()
	cursor.execute('PRAGMA foreign_keys=ON')
	cursor.close()


@contextmanager
def create_qtimer(configPath, defaultsPath):
	CoreLogger.debug('QTimerCore created through create_qtimer.')
	qtimer = QTimerCore(configPath, defaultsPath)
	try:
		yield qtimer
	finally:
		CoreLogger.debug('Control returned to create_qtimer, destroying core')
		qtimer.close()
		CoreLogger.debug('Destroying SQLSession')
		SQLSession.close_all()


def main():
	logging.config.fileConfig(DEFAULT_CONFIG_PATH)
	with create_qtimer(CONFIG_PATH, DEFAULT_CONFIG_PATH) as qtimer:
		args = qtimer.parseArgs()
		qtimer.executeCommand(args)
