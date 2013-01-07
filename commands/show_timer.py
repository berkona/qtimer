from datetime import datetime, timedelta

from commands.command import Command
from model import Timer, Session
from util import format_time
from strings import strings


class ShowTimer(Command):

	COMMAND_IDENTIFIER = 'show'
	COMMAND_HELP = strings['command_show']

	def runCommand(self, args, program):
		args = program.parseArgs(['find', 'timers', '-a'])
		return program.executeCommand(args)
