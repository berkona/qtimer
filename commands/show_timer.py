from command import Command
from strings import strings
from datetime import datetime, timedelta
from qtimer import format_time

class ShowTimer(Command):

	COMMAND_IDENTIFIER = 'show'
	COMMAND_HELP = strings['command_show']

	def runCommand(self, args, program):
		self.program = program
		query = '''
			SELECT t.id as id, g.name as group_name,
				t.name as name, note, start, end
			FROM timers t LEFT JOIN groups g ON t.group_id = g.id
				WHERE end IS NULL
		'''

		rows = map(self._formatTimer, program.conn.execute(query))
		program.outputRows(rows=rows, header=strings['timer_header'],
			weights=(0.1, 0.2, 0.2, 0.15, 0.15, 0.2))

	def _formatTimer(self, row):
		formattedStart = format_time(row['start'])
		end = row['end'] if row['end'] else datetime.utcnow()
		duration = self.program.round_time(end - row['start'])
		return (row['id'], row['name'], row['group_name'], formattedStart,
			duration, row['note'])
