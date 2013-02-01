from qtimer.commands.command import Command
from qtimer.strings import strings


class RefreshObjects(Command):

	COMMAND_IDENTIFIER = 'refresh'
	COMMAND_HELP = strings['command_refresh']

	def runCommand(self, args, program, core):
		core.sync()
