#! /usr/bin/env python3

# System imports
from datetime import datetime, timedelta
from os import path, makedirs

import argparse
import configparser
import sqlite3


# Custom imports
from strings import strings
import tz


# Plugin imports
from activecollab.library import ACRequest
# import plugins.freshbooks as freshbooks


DB_VERSION = 27
CONFIG_NAME = 'qtimer.cfg'
SCHEMA_SCRIPT = 'schema.sql'
DATA_NAME = 'timers v%d.db' % DB_VERSION


class QTimer:
    def __init__(self, config):
        for n, v in config.items():
            setattr(self, n, v)

        self.lastSynced = None
        self.cacheFunction = {
            'activecollab': self._syncAC,
            'freshbooks': self._syncFB
        }.get(self.accountType, self._noOp)

    def run(self):
        try:
            self._initDB()
            return {
                'start': self._startTimer,
                'end': self._endTimer,
                'show': self._showTimer,
                'edit': self._editTimer,
                'assign': self._assignGroup,
                'find': self._find,
                'refresh': self._sync,
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        # Set 'None' group by default
        groupId = self._findGroupId(self.group) if self.group else 1

        # If group is not None and groupId is still 1, we need to create this group
        if (self.group and groupId == 1):
            with self.conn:
                groupId = self.conn.execute('''INSERT INTO groups(name)
                    VALUES (?)''', [self.group]).lastrowid

        query = '''
            INSERT INTO timers(name, note, start, group_id)
                VALUES (?, ?, ?, ?)
        '''

        with self.conn:
            self.conn.execute(query, (self.name, self.note,
                    self._roundTime(datetime.utcnow()), groupId))

        self.name = None
        self.showAll = False
        self._showTimer()

    def _endTimer(self):
        query = '''
            UPDATE timers SET end = ? WHERE name LIKE ? AND end IS NULL
        '''

        with self.conn:
            self.conn.execute(query,
                (self._roundTime(datetime.utcnow()), self.name))

        self.name = None
        self.showAll = False
        self._showTimer()

    def _showTimer(self):
        query = '''
            SELECT t.id as id, g.name as group_name,
                t.name as name, note, start, end
            FROM timers t JOIN groups g ON t.group_id = g.id
                WHERE end IS NULL
        '''

        for row in self.conn.execute(query):
            print(self._formatTimer(row))

    def _editTimer(self):
        values = []
        params = []
        if (self.note):
            values.append('note = ?')
            params.append(self.note)
        if (self.start):
            values.append('start = ?')
            params.append(self.start)
        if (self.end):
            values.append('end = ?')
            params.append(self.end)

        params.append(self.name)

        query = 'UPDATE timers SET %s WHERE name LIKE ?' % ', '.join(values)
        with self.conn:
            self.conn.execute(query, params)

    def _assignGroup(self):
        query = '''
            UPDATE groups SET project_id = ?, ticket_id = ? WHERE name LIKE ?
        '''
        with self.conn:
            self.conn.execute(query, (self.project, self.ticket, self.name))

    def _find(self):
        {
            "groups": self._findGroups,
            "timers": self._findTimers,
            "tickets": self._findTickets,
            "projects": self._findProjects
        }.get(self.type, self._noOp)()

    def _findTimers(self):
        query = '''
            SELECT t.id as id, g.name as group_name,
                t.name as name, note, start, end
            FROM timers t JOIN groups g ON t.group_id = g.id
        '''

        where = []
        params = []

        if self.name:
            where.append('t.name LIKE ?')
            params.append('%' + self.name + '%')

        if self.group:
            where.append('g.name LIKE ?')
            params.append('%' + self.group + '%')

        if self.id:
            where.append('t.id = %d' % self.id)

        formatted = self._formatSelect(query, where)

        # print(formatted)

        for row in self.conn.execute(formatted, params):
            print(self._formatTimer(row))

    def _findTickets(self):
        self._syncConditionally()
        query = '''
            SELECT p.id as project_id, t.ticket_id as ticket_id, t.name as ticket_name,
                p.name as project_name
            FROM tickets t INNER JOIN projects p ON t.project_id = p.id
        '''
        formatStr = '%d - %s (%d - %s)'
        where = []
        params = []

        if self.name:
            where.append('ticket_name LIKE ?')
            params.append('%' + self.name + '%')

        if self.project:
            where.append('project_name LIKE ?')
            params.append('%' + self.project + '%')

        if self.id:
            where.append('t.id = %d' % self.id)

        formatted = self._formatSelect(query, where) \
            + ' ORDER BY project_id ASC, ticket_id ASC'

        rows = []
        maxLen = 0
        for row in self.conn.execute(formatted, params):
            rowStr = formatStr %  (row['ticket_id'], row['ticket_name'],
                row['project_id'], row['project_name'])
            length = len(rowStr)
            if length > maxLen:
                maxLen = length
            rows.append(rowStr)

        if self.verbose:
            print(strings['debug_query'])
            print(formatted.strip('\n '))
            print()

        print(strings['tickets_header'])
        print('-' * (maxLen + 5))
        print('\n'.join(rows))

    def _findProjects(self):
        self._syncConditionally()
        query = '''
            SELECT p.id as id, p.name as name FROM projects p
        '''
        formatStr = '%-10d%-10s'
        where = []
        params = []

        if self.name:
            where.append('name LIKE ?')
            params.append('%' + self.name + '%')

        if self.id:
            where.append('id = %d' % self.id)

        formatted = self._formatSelect(query, where) + ' ORDER BY id ASC'

        if self.verbose:
            print(strings['debug_query'])
            print(formatted.strip('\n '))
            print()

        print(strings['projects_header'])
        for row in self.conn.execute(formatted, params):
            print(formatStr % (row['id'], row['name']))

    def _findGroups(self):
        self._syncConditionally()
        query = '''
            SELECT id, name FROM groups g
        '''
        formatStr = '%-10d%-10s'
        where = []
        params = []

        if self.name:
            where.append('name LIKE ?')
            params.append('%' + self.name + '%')

        if self.id:
            where.append('id = %d' % self.id)

        formatted = self._formatSelect(query, where) + ' ORDER BY id ASC'

        if self.verbose:
            print(strings['debug_query'])
            print(formatted.strip('\n '))
            print()

        print(strings['groups_header'])
        for row in self.conn.execute(formatted, params):
            print(formatStr % (row['id'], row['name']))

    def _noOp(self):
        raise RuntimeError(strings['no_op'])

    def _initDB(self):
        needsSchemaUpgrade = not path.exists(self.dataPath)

        self.conn = sqlite3.connect(self.dataPath,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('pragma foreign_keys=ON')

        for row in self.conn.execute('pragma foreign_keys'):
            if (row and not row[0]):
                raise RuntimeError(strings['no_fk'] % sqlite3.sqlite_version)

        if not needsSchemaUpgrade:
            curs = self.conn.execute('''SELECT max(sync_date) as
                "sync_date [timestamp]" FROM (
                SELECT sync_date FROM tickets t
                UNION ALL
                SELECT sync_date FROM projects p
            ) ''')
            row = curs.fetchone()
            self.lastSynced = row[0]
            return

        print(strings['new_db'] % DB_VERSION)
        with self.conn:
            with open(self.schemaPath, 'rt') as f:
                schema = f.read()
            self.conn.executescript(schema)

        self._sync()

    def _formatSelect(self, query, where):
        output = query
        if (where):
            output += ' WHERE ' + ' AND '.join(where)
        return output

    def _formatTimer(self, row):
        formattedStart = formatTime(row['start'])
        end = row['end'] if row['end'] else datetime.utcnow()
        duration = self._roundTime(end - row['start'])
        return '#%d %s (%s): %s - %s %s' % (row['id'], row['name'],
            row['group_name'], formattedStart, duration,
            row['note'] if row['note'] else '')

    def _syncConditionally(self):
        if self.url == None or self.token == None or self.cacheFunction == None:
            raise RuntimeError(strings['bad_config'])

        lifetime = timedelta(minutes=self.cacheLifetime)

        if not self.lastSynced or datetime.utcnow() - self.lastSynced > lifetime:
            self._sync()

    def _sync(self):
        print(strings['old_data'] % (self.accountType, self.url))
        self.cacheFunction()
        self.lastSync = datetime.utcnow()

    def _syncAC(self):
        projectInsert = '''
            INSERT OR REPLACE INTO projects(id, name) VALUES (?, ?)
        '''

        ticketInsert = '''
            INSERT OR REPLACE INTO tickets(id, ticket_id, project_id, name)
                VALUES (?, ?, ?, ?)
        '''

        with self.conn:
            req = ACRequest('projects', ac_url=self.url, api_key=self.token)
            # print(req.command_url)
            for project in req.execute():
                # print(project)
                self.conn.execute(projectInsert, (project['id'], project['name']))

                req = ACRequest('projects', item_id=project['id'],
                    subcommand='tickets', ac_url=self.url, api_key=self.token)

                for ticket in req.execute():
                    # print(ticket)
                    self.conn.execute(ticketInsert,
                        (ticket['id'], ticket['ticket_id'],
                            project['id'], ticket['name']))

    def _syncFB(self):
        pass

    def _findGroupId(self, group):
        groupId = 1  # This is the 'None' group
        curs = self.conn.execute('''
            SELECT id FROM groups WHERE name LIKE ?
        ''', [group])
        row = curs.fetchone()
        if (row):
            groupId = row[0]
        return groupId

    def _roundTime(self, dt=None, roundTo=60):
        if dt == None:
            dt = datetime.utcnow()

        seconds = (dt - dt.min).seconds
        # // is a floor division not a comment on the following line
        rounding = (seconds + roundTo / 2) // roundTo * roundTo
        ms = dt.microseconds if hasattr(dt, 'microseconds') else 0
        return dt + timedelta(0, rounding - seconds, -ms)


def parseTime(dateStr):
    return datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


def formatTime(datetime):
    utc = datetime.replace(tzinfo=tz.UTC)
    return utc.astimezone(tz.Local).strftime('%x %H:%M')


def parseArgs():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title=strings['command_title'], dest='op',)

    parser_named = argparse.ArgumentParser(add_help=False)
    parser_named.add_argument('name', help=strings['command_name'])

    parser_start = subparsers.add_parser('start',  parents=[parser_named],
        help=strings['command_start'])

    parser_start.add_argument('-n', '--note', help=strings['command_start_note'])
    parser_start.add_argument('-g', '--group', help=strings['command_start_group'])

    subparsers.add_parser('end', parents=[parser_named],
        help=strings['command_end'])

    parser_edit = subparsers.add_parser('edit', parents=[parser_named],
        help=strings['command_edit'])

    parser_edit.add_argument('-n', '--note', help=strings['command_edit_note'])
    parser_edit.add_argument('-s', '--start', type=parseTime,
        help=strings['command_edit_start'])
    parser_edit.add_argument('-e', '--end', type=parseTime,
        help=strings['command_edit_end'])
    parser_edit.add_argument('-g', '--group', help=strings['command_edit_group'])

    parser_assign = subparsers.add_parser('assign', parents=[parser_named],
        help=strings['command_assign'])
    parser_assign.add_argument('project', help=strings['command_assign_project'])
    parser_assign.add_argument('ticket', help=strings['command_assign_ticket'])

    subparsers.add_parser('show', help=strings['command_show'])

    parser_find = subparsers.add_parser('find', help=strings['command_find'])

    common_find_parser = argparse.ArgumentParser(add_help=False)
    common_find_parser.add_argument('-n', '--name', help=strings['command_find_name'])
    common_find_parser.add_argument('-i', '--id', type=int,
        help=strings['command_find_id'])

    subparser_find = parser_find.add_subparsers(dest='type',
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

    parser_post = subparsers.add_parser('post', parents=[common_find_parser],
        help=strings['command_post'])
    parser_post.add_argument('-g', '--group', help=strings['command_find_group'])

    subparsers.add_parser('refresh', 
        help=strings['command_refresh'])


    config = vars(parser.parse_args())
    if not config['op']:
        parser.print_help()
        raise RuntimeError(strings['no_op'])

    return config


def main():
    config = None

    try:
        config = parseArgs()
    except RuntimeError:
        return -1

    configRoot = path.expanduser('~/.qtimer')
    if not path.exists(configRoot):
        makedirs(configRoot)

    configPath = path.join(configRoot, CONFIG_NAME)
    dataPath = path.join(configRoot, DATA_NAME)

    userConfig = configparser.ConfigParser()
    scriptRoot = path.dirname(path.realpath(__file__))
    with open(path.join(scriptRoot, 'default.cfg')) as defaultFile:
        userConfig.readfp(defaultFile)

    if not path.exists(configPath):
        raise RuntimeError(strings['no_config'])
    userConfig.read(configPath)

    config.update({
        'verbose': userConfig['debug']['verbose'],
        'dataPath': dataPath,
        'schemaPath': path.join(scriptRoot, SCHEMA_SCRIPT),
        'accountType': userConfig['account']['type'],
        'url': userConfig['account']['url'],
        'token': userConfig['account']['token'],
        'cacheLifetime': int(userConfig['account']['cache_lifetime']),
    })

    QTimer(config).run()

    return 0

if __name__ == '__main__':
    exit(main())
