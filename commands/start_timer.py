from command import Command
from strings import strings
from datetime import datetime

class StartTimer(Command):

	COMMAND_IDENTIFIER = 'start'
	COMMAND_HELP = strings['command_start']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('-n', '--note', help=strings['command_start_note'])
		parser.add_argument('-g', '--group', help=strings['command_start_group'])

	def runCommand(self, args, program):
		# Set 'None' group by default
		groupId = program.findGroupId(args.group) if args.group else 1

		# If group is not None and groupId is still 1, we need to create this
		# group
		if (args.group and groupId == 1):
			with program.conn:
				groupId = program.conn.execute('''INSERT INTO groups(name)
					VALUES (?)''', [args.group]).lastrowid

		query = '''
			INSERT INTO timers(name, note, start, group_id)
				VALUES (?, ?, ?, ?)
		'''

		with program.conn:
			program.conn.execute(query, (args.name, args.note,
				program.round_time(datetime.utcnow()), groupId))

		args = program.parseArgs(['show'])
		program.executeCommand(args.op, args)
