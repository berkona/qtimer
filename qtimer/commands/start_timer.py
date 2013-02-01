from datetime import datetime, timedelta

from qtimer.commands.command import Command
from qtimer.model import Timer, Session
from qtimer.util import autocommit
from qtimer.strings import strings


class StartTimer(Command):

	COMMAND_IDENTIFIER = 'start'
	COMMAND_HELP = strings['command_start']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('-t', '--ticket', type=int, help=strings['command_start_group'])

	def runCommand(self, args, program, core):
		session = Session(start=core.roundTime(datetime.utcnow()))
		timer = Timer(name=args['name'], ticket_id=args['ticket'], sessions=[session])
		with autocommit(core.session) as sql:
			sql.add(timer)

		args = program.parseArgs(['show'])
		program.executeCommand(args)

		return timer
