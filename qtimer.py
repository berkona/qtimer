#! /usr/bin/env python

# import freshbooks
import argparse
import configparser
import sqlite3
from strings import STRINGS
import tz

from activecollab.library import ACRequest
from datetime import datetime, timedelta
from os import path, makedirs

DB_VERSION = 21
CONFIG_NAME = 'qtimer.cfg'
SCHEMA_SCRIPT = 'qtimer.schema.sql'
DATA_NAME = 'timers v%d.db' % DB_VERSION


class QTimer:
    def __init__(self, config):
        for n, v in config.items():
            setattr(self, n, v)

        self.lastSynced = None
        self.cacheFunction = {
            'activecollab': self._syncProjectsAC,
            'freshbooks': self._syncProjectsFB
        }.get(self.accountType, None)

    def run(self):
        try:
            self._initDB()
            return {
                'start': self._startTimer,
                'end': self._endTimer,
                'show': self._showTimer,
                'edit': self._editTimer,
                'assign': self._assignGroup,
                'find': self._find
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        # Set 'None' group by default
        groupId = self._findGroupId(self.group) if self.group else 1

        # If group is not None and groupId is still 1, we need to create this group
        if (self.group and groupId == 1):
            with self.conn:
                self.conn.execute('''INSERT INTO groups(name)
                    VALUES (?)''', [self.group])
            groupId = self.conn.lastrowid

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

        formatted = self._formatSelect(query, where)

        # print(formatted)

        for row in self.conn.execute(formatted, params):
            print(self._formatTimer(row))

    def _findTickets(self):
        self._syncProjects()
        query = '''
            SELECT t.id as id, t.ticket_id as ticket_id, t.name as ticket_name,
                p.name as project_name
            FROM tickets t INNER JOIN projects p ON t.project_id = p.id
        '''
        formatStr = '#%d (%d) - %s (%s)'
        where = []
        params = []

        if self.name:
            where.append('ticket_name LIKE ?')
            params.append('%' + self.name + '%')

        if self.project:
            where.append('project_name LIKE ?')
            params.append('%' + self.project + '%')

        formatted = self._formatSelect(query, where) \
            + ' ORDER BY project_id ASC, ticket_id ASC'

        # print(formatted)

        for row in self.conn.execute(formatted, params):
            print(formatStr % (row['id'], row['ticket_id'],
                row['ticket_name'], row['project_name']))

    def _findProjects(self):
        self._syncProjects()
        query = '''
            SELECT p.id as id, p.name as project_name FROM projects p
        '''
        formatStr = '#%d - %s'
        where = []
        params = []

        if self.name:
            where.append('project_name LIKE ?')
            params.append('%' + self.name + '%')

        formatted = self._formatSelect(query, where) + ' ORDER BY id ASC'

        # print(formatted)

        for row in self.conn.execute(formatted, params):
            print(formatStr % (row['id'], row['project_name']))

    def _noOp(self, op=None):
        if not op:
            op = self.op
        raise RuntimeError('There is no defined operation for the command %s.' % op)

    def _initDB(self):
        needsSchemaUpgrade = not path.exists(self.dataPath)

        self.conn = sqlite3.connect(self.dataPath,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('pragma foreign_keys=ON')

        for row in self.conn.execute('pragma foreign_keys'):
            if (row and not row[0]):
                raise RuntimeError(
                    'Cannot enable foreign keys, platform sqlite3 version ' + sqlite3.sqlite_version
                )

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

        print('Creating new database for schema version: ', DB_VERSION)
        with self.conn:
            with open(self.schemaPath, 'rt') as f:
                schema = f.read()
            self.conn.executescript(schema)

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

    def _syncProjects(self):
        if self.url == None or self.token == None or self.cacheFunction == None:
            raise RuntimeError('Either url, token, or accountType is NULL, check config file')

        lifetime = timedelta(minutes=self.cacheLifetime)

        # print('Last Synced: ', formatTime(self.lastSynced),
        #    ', time elapsed: ', delta,
        #    ', configured lifetime: ', lifetime)

        if not self.lastSynced or datetime.utcnow() - self.lastSynced > lifetime:
            print('Cached remote info is too old, reloading from ' + self.url)
            self.cacheFunction()

        self.lastSync = datetime.utcnow()

    def _syncProjectsAC(self):
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

    def _syncProjectsFB(self):
        # TODO
        pass

    def _findGroupId(self, group):
        groupId = 1  # This is the 'None' group
        curs = self.conn.execute('''SELECT id FROM groups
                WHERE name LIKE ?''', [group])
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
    subparsers = parser.add_subparsers(title='Available commands', dest='op',)

    parser_start = subparsers.add_parser('start', help='Start a timer')
    parser_start.add_argument('name', help='Name of the timer to be created')
    parser_start.add_argument('-n', '--note', help='An optional note for this timer')
    parser_start.add_argument('-g', '--group', help='An optional group name')

    parser_end = subparsers.add_parser('end', help='End a currently running timer')
    parser_end.add_argument('name', help='Name of the timer to be stopped')

    parser_edit = subparsers.add_parser('edit', help='Edit a stopped timer')
    parser_edit.add_argument('name', help='Specify a timer to show details about')
    parser_edit.add_argument('-n', '--note', help='Note to set for this timer')
    parser_edit.add_argument('-s', '--start', type=parseTime, help='Start date to set for this timer')
    parser_edit.add_argument('-e', '--end', type=parseTime, help='Duration to set for this timer')
    parser_edit.add_argument('-g', '--group', help='Group name to set this timer to')

    parser_assign = subparsers.add_parser('assign', help='Assign a group to a ticket')
    parser_assign.add_argument('name', help='Group name to use to find group')
    parser_assign.add_argument('project', help='Project id to assign group to')
    parser_assign.add_argument('ticket', help='Ticket id to assign group to')

    subparsers.add_parser('show', help='List all running timers')

    parser_find = subparsers.add_parser('find',
        help='Show details about objects in database')
    parser_find.add_argument('-n', '--name',
        help='Specify a timer to show details about')
    parser_find.add_argument('type', choices=['timers', 'tickets', 'projects'],
        help='What type of object should we look for')
    parser_find.add_argument('-p', '--project',
        help='Find tickets in a project')
    parser_find.add_argument('-g', '--group',
        help='Show timers from a specific group')

    return (parser, vars(parser.parse_args()))


def main():
    parser = None
    config = None

    parser, config = parseArgs()

    # Check that we have a task to do
    if not config['op']:
        parser.print_help()
        return -1

    configRoot = path.expanduser('~/.qtimer')
    if not path.exists(configRoot):
        makedirs(configRoot)

    configPath = path.join(configRoot, CONFIG_NAME)
    dataPath = path.join(configRoot, DATA_NAME)

    userConfig = configparser.ConfigParser()
    scriptRoot = path.dirname(path.realpath(__file__))
    with open(path.join(scriptRoot, CONFIG_NAME)) as defaultFile:
        userConfig.readfp(defaultFile)

    userConfig.read(configPath)

    config.update({
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
