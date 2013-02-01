from datetime import datetime, timedelta

from qtimer.commands.command import Command
from qtimer.model import Timer, Session
from qtimer.util import format_time
from qtimer.strings import strings


class ShowTimer(Command):

	COMMAND_IDENTIFIER = 'show'
	COMMAND_HELP = strings['command_show']

	def runCommand(self, args, program, core):
		args = program.parseArgs(['find', 'timers', '-a'])
		return program.executeCommand(args)
