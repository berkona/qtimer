#! /usr/bin/env python3

# System imports
from datetime import datetime, timedelta
from os import path, makedirs, listdir
from importlib import import_module

import argparse
import configparser
import sqlite3


# Custom imports
from strings import strings
import terminalsize
import tz

PLUGIN_MOD = 'plugins.%s.plugin'

COMMAND_MOD = 'commands.%s'
COMMANDS_FOLDER = 'commands'

DB_VERSION = 29
DATA_NAME = 'timers v%d.db' % DB_VERSION


class QTimer:

	def __init__(self):
		self.commands = {}

		scriptRoot = path.dirname(path.realpath(__file__))
		commandPath = path.join(scriptRoot, COMMANDS_FOLDER)
		files = (path.splitext(item)[0] for item in listdir(commandPath)
			if (not item == '__init__.py') and path.isfile(path.join(commandPath, item)))

		for f in files:
			self.importCommand(f)


		self.args = self.parseArgs()

		configRoot = path.expanduser('~/.qtimer')
		if not path.exists(configRoot):
			makedirs(configRoot)

		configPath = path.join(configRoot, 'qtimer.cfg')

		userConfig = configparser.ConfigParser()
		with open(path.join(scriptRoot, 'default.cfg')) as defaultFile:
			userConfig.readfp(defaultFile)

		if not path.exists(configPath):
			raise RuntimeError(strings['no_config'])

		userConfig.read(configPath)

		# Store some vital pathnames for later
		self.dataPath = path.join(configRoot, DATA_NAME)
		self.schemaPath = path.join(scriptRoot, 'schema.sql')

		# userConfig fields
		self.accountType = userConfig['account']['type']
		self.url = userConfig['account']['url']
		self.token = userConfig['account']['token']
		self.cacheLifetime = int(userConfig['account']['cache_lifetime'])
		self.rounding = 60 * int(userConfig['timers']['rounding'])

		verbose = userConfig['debug']['verbose'].lower() == 'true'

		# Inject a couple things into args based on userConfig/systemConfig
		setattr(self.args, 'verbose', (self.args.verbose or verbose))
		setattr(self.args, 'consoleSize', terminalsize.get_terminal_size())

		# This also has the side-effect of initializing the database
		self.lastSynced = self.conn.execute('''
		SELECT max(sync_date) as "sync_date [timestamp]" FROM (
			SELECT sync_date FROM tickets t
			UNION ALL
			SELECT sync_date FROM projects p
		) ''').fetchone()[0]

	@property
	def plugin(self):
		if hasattr(self, '_plugin'):
			return self._plugin

		if not (self.url and self.token and self.accountType):
			raise RuntimeError(strings['bad_config'])

		try:
			mod = import_module(PLUGIN_MOD % self.accountType)
			self._plugin = mod.load_qtimer_plugin(self.url, self.token)
			return self._plugin
		except ImportError:
			raise RuntimeError(strings['no_plugin_found'] % self.accountType)

	@property
	def conn(self):
		if (hasattr(self, '_conn')):
			return self._conn

		needsSchemaUpgrade = not path.exists(self.dataPath)

		self._conn = sqlite3.connect(self.dataPath,
			detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
		self._conn.row_factory = sqlite3.Row
		self._conn.execute('pragma foreign_keys=ON')

		if needsSchemaUpgrade:
			print(strings['new_db'] % DB_VERSION)
			with self._conn:
				with open(self.schemaPath, 'rt') as f:
					schema = f.read()
				self._conn.executescript(schema)

		return self._conn

	def run(self):
		try:
			return self.executeCommand(self.args.op, self.args)
		finally:
			self.conn.close()

	def parseArgs(self, argsOverride=None):
		parser = argparse.ArgumentParser()
		parser.add_argument('-v', '--verbose', action='store_true', default=False)

		subparsers = parser.add_subparsers(title=strings['command_title'], dest='op')

		for identifier, command in self.commands.items():
			if hasattr(command, 'COMMAND_HELP'):
				subparser = subparsers.add_parser(identifier, help=command.COMMAND_HELP)
			else:
				subparser = subparsers.add_parser(identifier)
			command.addArguments(subparser)

		args = parser.parse_args(argsOverride)
		if not args.op:
			parser.print_help()
			raise RuntimeError(strings['no_op'])

		return args

	def importCommand(self, f):
		modName = COMMAND_MOD % f

		# Predict the class name to be the TitleCase of the script mod
		className = f.title().replace('_', '')
		mod = import_module(modName)
		command = getattr(mod, className)()

		if not hasattr(command, 'COMMAND_IDENTIFIER'):
			raise RuntimeError('Command %s must declare an ID' % modName)

		self.commands[command.COMMAND_IDENTIFIER] = command

	def executeCommand(self, op, args):
		command = self.commands.get(op, None)
		if not command:
			raise RuntimeError('No command found matching ' + op)
		command.runCommand(args, self)

	def formatSelect(self, query, where):
		output = query
		if (where):
			output += ' WHERE ' + ' AND '.join(where)
		return output

	def logQuery(self, formatted):
		if not self.args.verbose: return
		print(strings['debug_query'])
		print(formatted.strip('\n '))
		print()

	def outputRows(self, rows = [], header = (), weights = ()):
		totalWeight = sum(weights)
		if (totalWeight > 1 or totalWeight < 0.99):
			raise RuntimeError('The sum of all weights must be about 1, totalWeight: %f' % totalWeight)

		totalWidth = self.args.consoleSize[0]
		widths = []
		formatStr = ''
		for weight in weights:
			width = int(totalWidth * weight)
			formatStr += '%-' + str(width) + 's'
			widths.append(width)


		print(formatStr % header)
		print('-' * totalWidth)
		for row in rows:
			items = []
			for i, item in enumerate(row):
				if isinstance(item, str) and len(item) > widths[i]:
					item = smart_truncate(item, widths[i])
				items.append(item)
			print(formatStr % tuple(items))

	def syncConditionally(self):
		lifetime = timedelta(minutes=self.cacheLifetime)

		if (not self.lastSynced
			or datetime.utcnow() - self.lastSynced > lifetime):
			self.sync()

	def sync(self):
		print(strings['old_data'] % (self.accountType, self.url))

		projectInsert = '''
			INSERT OR REPLACE INTO projects(id, name) VALUES (?, ?)
		'''

		ticketInsert = '''
			INSERT OR REPLACE INTO tickets(id, ticket_id, project_id, name)
				VALUES (?, ?, ?, ?)
		'''

		with self.conn:
			for project in self.plugin.listProjects():
				self.conn.execute(projectInsert,
					(project['id'], project['name']))

				for ticket in self.plugin.listTickets(project['id']):
					self.conn.execute(ticketInsert,
						(ticket['id'], ticket['ticket_id'],
							project['id'], ticket['name']))

		self.lastSync = datetime.utcnow()

	def findGroupId(self, group):
		groupId = 1  # This is the 'None' group
		curs = self.conn.execute('''
			SELECT id FROM groups WHERE name LIKE ?
		''', [group])
		row = curs.fetchone()
		if (row):
			groupId = row[0]
		return groupId

	def round_time(self, dt):
		roundTo = self.rounding
		seconds = (dt - dt.min).seconds
		# // is a floor division not a comment on the following line
		rounding = (seconds + roundTo / 2) // roundTo * roundTo
		ms = dt.microseconds if hasattr(dt, 'microseconds') else 0
		ret = dt + timedelta(0, rounding - seconds, -ms)
		return ret

def smart_truncate(content, length=100, suffix='...'):
	length = length - len(suffix)
	if len(content) <= length:
		return content
	else:
		return content[:length].rsplit(' ', 1)[0] + suffix

def parse_time(dateStr):
	return datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


def format_time(datetime):
	utc = datetime.replace(tzinfo=tz.UTC)
	return utc.astimezone(tz.Local).strftime('%x %H:%M')

if __name__ == '__main__':
	exit(QTimer().run())
