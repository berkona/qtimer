from qtimer import smart_truncate, format_time
from datetime import datetime, timedelta
from command import Command
from strings import strings

import argparse

class FindObject(Command):

	'''
	Required. A unique string key which allows the program to determine which
	command it should run. Two commands with the same identifier is unsupported.
	'''
	COMMAND_IDENTIFIER = 'find'

	''' Set an optional help message for this command. '''
	COMMAND_HELP = strings['command_find']

	def addArguments(self, parser):
		# Parent parser that has ability to search for a name or primary key
		common_find_parser = argparse.ArgumentParser(add_help=False)
		common_find_parser.add_argument('-n', '--name',
			help=strings['command_find_name'])
		common_find_parser.add_argument('-i', '--id', type=int,
			help=strings['command_find_id'])

		subparser_find = parser.add_subparsers(dest='type',
			title='What type of object should we look for')

		parsers_find_timers = subparser_find.add_parser('timers',
			parents=[common_find_parser])
		parsers_find_timers.add_argument('-g', '--group',
			help=strings['command_find_group'])

		parsers_find_tickets = subparser_find.add_parser('tickets',
			parents=[common_find_parser])
		parsers_find_tickets.add_argument('-p', '--project',
			help=strings['command_find_project'])

		subparser_find.add_parser('projects', parents=[common_find_parser])
		subparser_find.add_parser('groups', parents=[common_find_parser])

	def runCommand(self, args, program):
		program.syncConditionally()
		self.program = program
		{
			"groups": self._findGroups,
			"timers": self._findTimers,
			"tickets": self._findTickets,
			"projects": self._findProjects
		}.get(args.type)(args, program)

	def _findTimers(self, args, program):
		query = '''
			SELECT t.id as id, g.name as group_name,
				t.name as name, note, start, end
			FROM timers t LEFT JOIN groups g ON t.group_id = g.id
		'''

		where = []
		params = []

		if args.name:
			where.append('t.name LIKE ?')
			params.append('%' + args.name + '%')

		if args.group:
			where.append('g.name LIKE ?')
			params.append('%' + args.group + '%')

		if args.id:
			where.append('t.id = %d' % args.id)

		formatted = program.formatSelect(query, where)
		rows = map(self._formatTimer, program.conn.execute(formatted, params))

		program.logQuery(formatted)
		program.outputRows(rows=rows, header=strings['timer_header'],
			weights=(0.1, 0.2, 0.2, 0.15, 0.15, 0.2))

	def _findGroups(self, args, program):
		query = '''
			SELECT g.id, g.name, i.project_id, i.project_name, i.ticket_id,
				i.ticket_name
			FROM groups g LEFT JOIN tickets_extra i ON (
				g.project_id = i.project_id AND g.ticket_id = i.ticket_id
			)
		'''
		where = []
		params = []

		if args.name:
			where.append('name LIKE ?')
			params.append('%' + self.name + '%')

		if args.id:
			where.append('id = %d' % self.id)

		formatted = program.formatSelect(query, where) + ' ORDER BY id ASC'
		rows = program.conn.execute(formatted, params)

		program.logQuery(formatted)
		program.outputRows(rows=rows, header=strings['groups_header'],
			weights=(0.05, 0.15, 0.05, 0.3, 0.05, 0.4))

	def _findTickets(self, args, program):
		query = '''
			SELECT * FROM tickets_extra
		'''
		where = []
		params = []

		if args.name:
			where.append('ticket_name LIKE ?')
			params.append('%' + args.name + '%')

		if args.project:
			where.append('project_name LIKE ?')
			params.append('%' + args.project + '%')

		if args.id:
			where.append('ticket_id = %d' % args.id)

		formatted = program.formatSelect(query, where) \
			+ ' ORDER BY project_id ASC, ticket_id ASC'

		rows = program.conn.execute(formatted, params)

		program.logQuery(formatted)
		program.outputRows(rows=rows, header=strings['tickets_header'],
			weights=(0.05, 0.4, 0.05, 0.5))

	def _findProjects(self, args, program):
		query = '''
			SELECT p.id as id, p.name as name FROM projects p
		'''
		where = []
		params = []

		if args.name:
			where.append('name LIKE ?')
			params.append('%' + args.name + '%')

		if args.id:
			where.append('id = %d' % args.id)

		formatted = program.formatSelect(query, where) + ' ORDER BY id ASC'

		rows = program.conn.execute(formatted, params)

		program.logQuery(formatted)
		program.outputRows(rows=rows, header=strings['projects_header'],
			weights=(0.1, 0.9))

	def _formatTimer(self, row):
		formattedStart = format_time(row['start'])
		end = row['end'] if row['end'] else datetime.utcnow()
		duration = self.program.round_time(end - row['start'])
		return (row['id'], row['name'], row['group_name'], formattedStart,
			duration, row['note'])
