from datetime import datetime, timedelta

from sqlalchemy import Column
from model import Timer, Session, Ticket, Project
from util import smart_truncate, format_time
from commands.command import Command
from strings import strings

import argparse

DISPLAYED_FIELDS = {
	'timers': ( 'id', 'name', 'start', 'duration', 'ticket', 'posted', ),
	'tickets': ( 'id', 'name', 'ticket_id', 'project_id', ),
	'projects': ( 'id', 'name', ),
}

DISPLAY_WEIGHTS = {
	'timers': (0.1, 0.18, 0.16, 0.1, 0.42, 0.04),
	'tickets': (0.1, 0.7, 0.1, 0.1)
}

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
		common_find_parser.add_argument('-i', '--id', help=strings['command_find_id'])

		subparser_find = parser.add_subparsers(dest='type',
			title='What type of object should we look for')

		parsers_find_timers = subparser_find.add_parser('timers',
			parents=[common_find_parser])
		parsers_find_timers.add_argument('-a', '--active',
			action='store_true', default=False)
		parsers_find_timers.add_argument('--inactive',
			action='store_true', default=False)
		parsers_find_timers.add_argument('-p', '--project')
		parsers_find_timers.add_argument('-t', '--ticket')

		parsers_find_tickets = subparser_find.add_parser('tickets',
			parents=[common_find_parser])
		parsers_find_tickets.add_argument('-p', '--project',
			help=strings['command_find_project'])

		subparser_find.add_parser('projects', parents=[common_find_parser])

	def runCommand(self, args, program):
		program.syncConditionally()

		sql = program.session
		ormClass = {
			"timers": Timer,
			"tickets": Ticket,
			"projects": Project,
		}.get(args.type)

		q = sql.query(ormClass)

		if hasattr(args, 'name') and args.name:
			q = q.filter(ormClass.name.like('%' + args.name + '%'))

		if hasattr(args, 'id') and args.id:
			q = q.filter(ormClass.id == args.id)

		if hasattr(args, 'project') and args.project:
			q = q.join(Project).filter(Project.name.like('%' + args.project + '%'))

		if hasattr(args, 'ticket') and args.ticket:
			q = q.join(Ticket).filter(Ticket.name.like('%' + args.ticket + '%'))

		if hasattr(args, 'active') and args.active:
			q = q.join(Session).filter(Session.end == None)

		if hasattr(args, 'inactive') and args.inactive:
			q = q.join(Session).filter(Session.end != None)

		# This determines the ordering of the tuple
		fieldNames = DISPLAYED_FIELDS.get(args.type)

		mapFunc = lambda i: self._formatRow(i, fieldNames, program)
		rows = map(mapFunc, q)
		header = tuple( [ s.replace('_', ' ').title() for s in fieldNames ] )
		weights = DISPLAY_WEIGHTS.get(args.type)
		program.outputRows(rows=rows, header=header, weights=weights)

		return q

	def _formatRow(self, row, fieldNames, program):
		items = vars(row)
		if isinstance(row, Timer):
			items['start'] = format_time(row.sessions[0].start)
			items['duration'] = timedelta()
			for session in row.sessions:
				end = session.end if session.end else datetime.utcnow()
				items['duration'] += (end - session.start)
			items['duration'] = program.roundTime(items['duration'])
			items['ticket'] = '%d: %s' % (row.ticket.id, row.ticket.name) \
				if row.ticket else None

		return tuple([ items[key] for key in fieldNames ])
