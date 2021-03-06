# This is intended to be run as the main file in a command line

from importlib import import_module
from os import path, listdir

import argparse
import logging

from qtimer.util import smart_truncate, LazyObject
from qtimer.core import create_qtimer
from qtimer.lib import terminalsize
from qtimer.strings import strings
from qtimer.env import *

OutputLogger = logging.getLogger('output')


class QTimerCommandLine(LazyObject):

	def __init__(self, core):
		super(self, QTimerCommandLine).__init__({
			'commands': self.loadCommands,
			'parser': self.loadParser,
		})
		self.core = core

	def loadCommands(self):
		commands = {}
		commandPath = path.join(SCRIPT_ROOT, 'commands')

		files = (path.splitext(item)[0] for item in listdir(commandPath)
			if (not (item == '__init__.py' or item == 'command.py'))
				and path.isfile(path.join(commandPath, item)))

		for f in files:
			key, command = self._importCommand(f)
			commands[key] = command

		return commands

	def loadParser(self):
		parser = argparse.ArgumentParser(prog=APP_NAME)
		parser.add_argument('--version',
			action='version', version='%(prog)s ' + VERSION)

		subparsers = parser.add_subparsers(title=strings['command_title'], dest='op')

		for identifier, command in self.commands.items():
			if hasattr(command, 'COMMAND_HELP'):
				subparser = subparsers.add_parser(identifier, help=command.COMMAND_HELP)
			else:
				subparser = subparsers.add_parser(identifier)
			command.addArguments(subparser)

		return parser

	def parseArgs(self, argsOverride=None):
		args = self.parser.parse_args(argsOverride)
		if not args.op:
			self.parser.print_help()

		return vars(args)

	def executeCommand(self, args):
		command = self.commands.get(args['op'], None)
		if not command:
			raise RuntimeError('No command found matching ' + args['op'])
		return command.runCommand(
			args=args, program=self, core=self.core
		)

	def outputRows(self, rows=[], header=(), weights=()):
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

		OutputLogger.info(formatStr % header)
		OutputLogger.info('-' * totalWidth)
		for row in rows:
			items = []
			for i, item in enumerate(row):
				if isinstance(item, str) and len(item) > widths[i]:
					item = smart_truncate(item, widths[i])
				items.append(item)
			OutputLogger.info(formatStr % tuple(items))

	def _importCommand(self, f):
		# Predict the class name to be the TitleCase of the script mod
		className = f.title().replace('_', '')
		mod = import_module(COMMANDS_MOD % f)
		command = getattr(mod, className)()

		if not hasattr(command, 'COMMAND_IDENTIFIER'):
			raise RuntimeError('Command %s must declare an ID' % (COMMANDS_MOD % f))

		return command.COMMAND_IDENTIFIER, command


def main():
	with create_qtimer(CONFIG_PATH) as core:
		cmd_line = QTimerCommandLine(core)
		args = cmd_line.parseArgs()
		cmd_line.executeCommand(args)
