from qtimer.commands.command import Command
from qtimer.util import autocommit
from qtimer.model import Timer
from qtimer.strings import strings

import logging

LOGGER = logging.getLogger(__name__)


class PostTimer(Command):

	COMMAND_IDENTIFIER = 'post'
	COMMAND_HELP = strings['command_post']

	def addArguments(self, parser):
		parser.add_argument('-i', '--id')
		parser.add_argument('-n', '--name')
		parser.add_argument('-p', '--project')
		parser.add_argument('-t', '--ticket')

	def runCommand(self, args, program, core):
		args = [
			'find', 'timers', '--inactive', '--with-ticket',
			'-i', args['id'], '-n', args['name'],
			'-p', args['project'], '-t', args['ticket']
		]
		args = program.parseArgs(args)
		timers = program.executeCommand(args)

		updatedTimers = []
		for timer in timers:
			try:
				core.plugin.postTimer(
					projectId=timer.ticket.project.id,
					ticketId=timer.ticket.ticket_id,
					data=timer
				)
				updatedTimers.append(timer.id)
			except:
				LOGGER.exception('Could not post timer.')

		if not updatedTimers:
			return

		values = { 'posted': True, }
		with autocommit(core.session) as session:
			session.query(Timer).filter(Timer.id.in_(updatedTimers)).update(values)
