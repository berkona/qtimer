from datetime import timedelta

from qtimer.model import Timer, Session, Ticket, Project
from qtimer.commands.command import Command
from qtimer.util import format_time
from qtimer.strings import strings

import argparse

DISPLAYED_FIELDS = {
    'timers': ( 'id', 'name', 'start', 'duration', 'ticket', 'status', 'posted', ),
    'tickets': ( 'id', 'name', 'ticket_id', 'project_id', ),
    'projects': ( 'id', 'name', ),
}

DISPLAY_WEIGHTS = {
    'timers': (0.1, 0.18, 0.16, 0.1, 0.3, 0.12, 0.04),
    'tickets': (0.1, 0.7, 0.1, 0.1)
}


# FIXME! This doesn't quite work anymore

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
        parsers_find_timers.add_argument('-s', '--status')
        parsers_find_timers.add_argument('-p', '--project')
        parsers_find_timers.add_argument('-t', '--ticket')

        parsers_find_tickets = subparser_find.add_parser('tickets',
            parents=[common_find_parser])
        parsers_find_tickets.add_argument('-p', '--project',
            help=strings['command_find_project'])

        subparser_find.add_parser('projects', parents=[common_find_parser])

    def runCommand(self, args, program, core):
        core.syncConditionally()

        sql = core.session

        ormClass = {
            "timers": Timer,
            "tickets": Ticket,
            "projects": Project,
        }.get(args['type'])

        q = sql.query(ormClass)

        if 'name' in args and args['name']:
            q = q.filter(ormClass.name.like('%' + args['name'] + '%'))

        if 'id' in args and args['id']:
            q = q.filter(ormClass.id == args['id'])

        if 'project' in args and args['project']:
            q = q.join(Project).filter(Project.name.like('%' + args['project'] + '%'))

        if 'ticket' in args and args['ticket']:
            q = q.join(Ticket).filter(Ticket.name.like('%' + args['ticket'] + '%'))

        if 'active' in args and args['active']:
            q = q.join(Session).filter(Session.end == None)

        if 'inactive' in args and args['inactive']:
            q = q.join(Session).filter(Session.end != None)

        # Filter by status if asked
        if 'status' in args and args['status']:
            q = filter(lambda t: args['status'].lower() in t.status.lower(), q)

        # This determines the ordering of the tuple
        fieldNames = DISPLAYED_FIELDS.get(args['type'])

        mapFunc = lambda i: self._formatRow(i, fieldNames, core)
        rows = map(mapFunc, q)

        header = tuple([ s.replace('_', ' ').title() for s in fieldNames ])
        weights = DISPLAY_WEIGHTS.get(args['type'])
        program.outputRows(rows=rows, header=header, weights=weights)

        return q

    def _formatRow(self, row, fieldNames, core):
        items = vars(row)
        if isinstance(row, Timer):
            items['start'] = format_time(row.start)
            items['duration'] = timedelta()
            items['duration'] = core.roundTime(row.duration)
            items['ticket'] = '%d: %s' % (row.ticket.id, row.ticket.name) \
                if row.ticket else None
            items['status'] = row.status.title()

        return tuple([ items[key] for key in fieldNames ])
