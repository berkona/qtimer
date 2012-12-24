from command import Command
from strings import strings
from qtimer import parse_time

class EditTimer(Command):

	'''
	Required. A unique string key which allows the program to determine which
	command it should run. Two commands with the same identifier is unsupported.
	'''
	COMMAND_IDENTIFIER = 'edit'

	''' Set an optional help message for this command. '''
	COMMAND_HELP = strings['command_edit']

	def runCommand(self, args, program):
		values = []
		params = []
		if (args.note):
			values.append('note = ?')
			params.append(args.note)
		if (args.start):
			values.append('start = ?')
			params.append(args.start)
		if (args.end):
			values.append('end = ?')
			params.append(args.end)

		params.append(args.name)

		query = 'UPDATE timers SET %s WHERE name LIKE ?' % ', '.join(values)
		with program.conn:
			program.conn.execute(query, params)

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('-n', '--note', help=strings['command_edit_note'])
		parser.add_argument('-s', '--start', type=parse_time,
			help=strings['command_edit_start'])
		parser.add_argument('-e', '--end', type=parse_time,
			help=strings['command_edit_end'])
		parser.add_argument('-g', '--group', help=strings['command_edit_group'])
