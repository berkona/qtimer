from qtimer.commands.command import Command
from qtimer.model import Session, Timer
from qtimer.util import autocommit
from qtimer.strings import strings

from datetime import datetime


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
		timer = core.session.query(Timer).filter(Timer.id == args['id']).one()
		session = Session(timer_id=timer.id, start=core.roundTime(datetime.utcnow()))
		with autocommit(core.session) as sql:
			sql.add(session)

		args = program.parseArgs([ 'find', 'timers', '--id', str(args['id']) ])
		return program.executeCommand(args)

	def addArguments(self, parser):
		'''
		Optional. Add all required args for this command.
		'''
		parser.add_argument('id', type=int, help=strings['command_id'])
		pass
