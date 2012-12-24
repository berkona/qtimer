from command import Command
from strings import strings

class AssignTimer(Command):

	COMMAND_IDENTIFIER = 'assign'
	COMMAND_HELP = strings['command_assign']

	def addArguments(self, parser):
		parser.add_argument('name', help=strings['command_name'])
		parser.add_argument('project', help=strings['command_assign_project'])
		parser.add_argument('ticket', help=strings['command_assign_ticket'])

	def runCommand(self, args, program):
		query = '''
			UPDATE groups SET project_id = ?, ticket_id = ? WHERE name LIKE ?
		'''
		with program.conn:
			program.conn.execute(query, (args.project, args.ticket, args.name))
