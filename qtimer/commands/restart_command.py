from qtimer.commands.command import Command


class RestartCommand(Command):

	'''
	Required. A unique string key which allows the program to determine which
	command it should run. Two commands with the same identifier is unsupported.
	'''
	COMMAND_IDENTIFIER = 'restart'

	''' Set an optional help message for this command. '''
	COMMAND_HELP = 'Restart a timer'

	def runCommand(self, args, program, core):
		'''
		Required. Perform the business logic associated with this command. You are
		given the args you added to the parser in addArguments as well as the
		program to run database commands, and access global data
		'''
		# IMPLEMENT ME
		pass

	def addArguments(self, parser):
		'''
		Optional. Add all required args for this command.
		'''
		# IMPLEMENT ME
		pass
