from datetime import datetime

from qtimer.commands.command import Command
from qtimer.model import Timer, Session
from qtimer.strings import strings
from qtimer.util import autocommit


class EndTimer(Command):

	COMMAND_IDENTIFIER = 'end'
	COMMAND_HELP = strings['command_end']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])

	def runCommand(self, args, program, core):
		with autocommit(core.session) as session:

			values = {
				Session.end: core.roundTime(datetime.utcnow())
			}

			session.query(Session).join(Timer).filter()\
			.filter(Timer.name.like('%' + args['name'] + '%'))\
			.filter(Session.end == None).update(values, 'fetch')

		args = program.parseArgs([ 'find', 'timers', '-n', args['name'] ])
		return program.executeCommand(args)
