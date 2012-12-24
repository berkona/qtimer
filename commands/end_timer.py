from command import Command
from strings import strings
from datetime import datetime

class EndTimer(Command):

	COMMAND_IDENTIFIER = 'end'
	COMMAND_HELP = strings['command_end']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])

	def runCommand(self, args, program):
		query = '''
			UPDATE timers SET end = ? WHERE name LIKE ? AND end IS NULL
		'''

		with program.conn:
			program.conn.execute(query,
				(program.round_time(datetime.utcnow()), args.name))

		args = program.parseArgs(['find', 'timers', '-n', args.name])
		program.executeCommand(args.op, args)
