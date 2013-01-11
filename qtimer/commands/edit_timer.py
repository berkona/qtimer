from qtimer.util import parse_time, autocommit

from qtimer.commands.command import Command
from qtimer.strings import strings

class EditTimer(Command):

	'''
	Required. A unique string key which allows the program to determine which
	command it should run. Two commands with the same identifier is unsupported.
	'''
	COMMAND_IDENTIFIER = 'edit'

	''' Set an optional help message for this command. '''
	COMMAND_HELP = strings['command_edit']

	def runCommand(self, args, program):
		with autocommit(program.session) as session:
			q = session.query(Timer).filter(Timer.name.like('%' + args['name'] + '%'))
			values = {}
			if args['start']:
				values[Timer.start] = args['start']
			if args['end']:
				values[Timer.end] = args['end']
			if args['ticket']:
				values[Timer.ticket_id] = args['ticket']

			return q.update(values)

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('-s', '--start', type=parse_time,
			help=strings['command_edit_start'])
		parser.add_argument('-e', '--end', type=parse_time,
			help=strings['command_edit_end'])
		parser.add_argument('-t', '--ticket', type=int, help=strings['command_edit_group'])
