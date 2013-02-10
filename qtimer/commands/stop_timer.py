from datetime import datetime

from qtimer.commands.command import Command
from qtimer.model import Session
from qtimer.strings import strings
from qtimer.util import autocommit


class StopTimer(Command):

	COMMAND_IDENTIFIER = 'stop'
	COMMAND_HELP = strings['command_end']

	def addArguments(self, parser):
		parser.add_argument('id', type=int, help=strings['command_id'])

	def runCommand(self, args, program, core):
		values = {
			Session.end: core.roundTime(datetime.utcnow())
		}

		with autocommit(core.session) as session:
			session.query(Session).filter(Session.timer_id == args['id'])\
				.filter(Session.end == None).update(values)

		args = program.parseArgs([ 'find', 'timers', '--id', str(args['id']) ])
		return program.executeCommand(args)
