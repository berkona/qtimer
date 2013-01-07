from datetime import datetime, timedelta

from commands.command import Command
from model import Timer, Session
from util import autocommit
from strings import strings


class StartTimer(Command):

	COMMAND_IDENTIFIER = 'start'
	COMMAND_HELP = strings['command_start']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('-t', '--ticket', type=int, help=strings['command_start_group'])

	def runCommand(self, args, program):
		timer = Timer(name=args.name, ticket_id=args.ticket)
		with autocommit(program.session) as sql:
			sql.add(timer)
			# Ensure timer has an id
			sql.commit()
			session = Session(start=program.roundTime(datetime.utcnow()), timer_id=timer.id)
			sql.add(session)

		args = program.parseArgs(['show'])
		program.executeCommand(args)

		return timer
