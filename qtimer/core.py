# Common core shared by the command line and the gui

# System imports
from datetime import datetime, timedelta
from contextlib import contextmanager
from importlib import import_module
from os import makedirs, path

import logging

import logging.config
import logging.handlers

# SQLALchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlalchemy as sa
import alembic.command

# Custom
from qtimer.model import Ticket, Project, PersistentVar
from qtimer.util import autocommit
from qtimer.strings import strings
from qtimer.config import Config
from qtimer.env import *


# This is what we use for writing to the database
SQLSession = sa.orm.sessionmaker()

CoreLogger = logging.getLogger(__name__)


class QTimerCore(object):

	def __init__(self, configPath):
		self.configPath = configPath

	@property
	def lastSynced(self):
		if hasattr(self, '_lastSynced'):
			return self._lastSynced
		q = self.session.query(PersistentVar)\
			.filter(PersistentVar.name.like('internal.lastSynced'))
		try:
			self._lastSynced = q.one().value
			CoreLogger.debug('lastSynced: %s, now: %s, delta: %s', self._lastSynced, datetime.utcnow(), datetime.utcnow() - self._lastSynced)
			return self._lastSynced
		except BaseException as e:
			CoreLogger.warn('Encountered exception: %s', repr(e))
			pass

	@property
	def session(self):
		if hasattr(self, '_session'):
			return self._session

		# This also has the side-effect of initializing the database
		alembic.command.upgrade(self.config, "head")

		CoreLogger.debug('sqlalchemy_url: %s', self.config.alembic.sqlalchemy_url)

		self.engine = sa.create_engine(
			self.config.alembic.sqlalchemy_url,
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

		mod = import_module(PLUGIN_MOD % accountType)
		self._plugin = mod.load_qtimer_plugin(url, token)
		return self._plugin

	@property
	def config(self):
		if hasattr(self, '_config'):
			return self._config

		self._config = Config(self.configPath)
		return self._config

	def syncConditionally(self):
		mins = int(self.config.account.cache_lifetime)
		lifetime = timedelta(minutes=mins)

		if (not self.lastSynced or (datetime.utcnow() - self.lastSynced) > lifetime):
			self.sync()

	def sync(self):
		CoreLogger.info(strings['old_data'], self.config.account.type,
			self.config.account.url)

		self.session.execute('PRAGMA foreign_keys=OFF')
		with autocommit(self.session) as session:
			# Truncate tables for new data, this is faster than merging
			session.query(Project).delete()
			session.query(Ticket).delete()
			CoreLogger.debug('Getting list of projects from remote')
			projects = self.plugin.listProjects()
			for project in projects:
				session.add(project)
				CoreLogger.debug("Getting list of tickets for pid '%s' from remote", project.id)
				tickets = self.plugin.listTickets(project.id)
				for ticket in tickets:
					session.add(ticket)

			lastSynced = PersistentVar(
				name='internal.lastSynced',
				value=datetime.utcnow()
			)
			session.merge(lastSynced)

		self.session.execute('PRAGMA foreign_keys=ON')

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


def set_sqlite_pragma(conn, conn_record):
	cursor = conn.cursor()
	cursor.execute('PRAGMA foreign_keys=ON')
	cursor.close()

event.listen(Engine, 'connect', set_sqlite_pragma)


def configure_logging(configPath):
	if not path.exists(configPath):
		raise RuntimeError(strings['no_config'])

	logging.config.fileConfig(configPath)

	# We hard-core this because we want to use a platform specific directory
	if not path.exists(path.dirname(LOG_PATH)):
		makedirs(path.dirname(LOG_PATH))

	handler = logging.handlers.RotatingFileHandler(LOG_PATH, backupCount=50)
	handler.formatter = logging.Formatter(
		'%(asctime)s|%(levelname)-7.7s [%(name)s] %(message)s', '%H:%M:%S')
	handler.doRollover()
	logging.getLogger().addHandler(handler)


@contextmanager
def create_qtimer(configPath):
	configure_logging(configPath)
	CoreLogger.debug('QTimerCore created through create_qtimer.')
	qtimer = QTimerCore(configPath)
	try:
		yield qtimer
	finally:
		CoreLogger.debug('Control returned to create_qtimer, destroying core')
		qtimer.close()
		CoreLogger.debug('Destroying SQLSession')
		SQLSession.close_all()
		CoreLogger.debug('Shutting down logging')
		logging.shutdown()
