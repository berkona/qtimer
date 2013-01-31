from qtimer.commands.command import Command
from qtimer.util import autocommit
from qtimer.strings import strings


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
			'find', 'timers', '--inactive', '-i', args['id'], '-n', args['name'],
			'-p', args['project'], '-t', args['ticket']
		]
		args = program.parseArgs(args)
		timers = program.executeCommand(args).all()
		print('Timers to be posted', repr(timers))
		# for timer in timers:
		# 	if not row.ticket_id:
		# 		continue
		# 	# TODO Setup testing env to test this
		# 	program.plugin.postTimer(projectId=row.ticket.project.id, ticketId=row.ticket.ticket_id, data=row)
