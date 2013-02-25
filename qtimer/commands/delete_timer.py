from qtimer.commands.command import Command
from qtimer.model import Timer, Session
from qtimer.strings import strings
from qtimer.util import autocommit


class DeleteTimer(Command):

	COMMAND_IDENTIFIER = 'delete'
	COMMAND_HELP = 'Delete a timer permanently.  Do not mess around with this command.  Will not allow you to delete a posted timer.'

	def addArguments(self, parser):
		parser.add_argument('id', type=int, help=strings['command_id'])

	def runCommand(self, args, program, core):
		with autocommit(core.session) as session:
			timer = session.query(Timer).filter(Timer.id == args['id']).filter(Timer.posted == False).one()
			session.query(Session).filter(Session.timer_id == timer.id).delete()
			session.delete(timer)
