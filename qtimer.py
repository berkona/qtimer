#! /usr/bin/env python

# import freshbooks
import argparse
import configparser
import sqlite3
import tz

from activecollab.library import ACRequest
from datetime import datetime, timedelta
from os import path, makedirs

DB_VERSION = 6
CONFIG_NAME = 'qtimer.cfg'
SCHEMA_SCRIPT = 'qtimer.schema.sql'
DATA_NAME = 'timers v%d.db' % DB_VERSION


class QTimer:
    def __init__(self, config):
        for n, v in config.items():
            setattr(self, n, v)

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
                'find': self._findProject
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        with self.conn:
            groupId = self._findGroupId(self.group) if self.group else -1

            # If row is not None and groupId is still -1, we need to create this group
            if (self.group and groupId == -1):
                self.conn.execute('''INSERT INTO groups(name)
                        VALUES (?)''', [self.group])
                groupId = self._findGroupId(self.group)

            self.conn.execute('''INSERT INTO timers(name, note, start, group_id)
                VALUES (?, ?, ?, ?) ''', (self.name, self.note,
                    self._roundTime(datetime.utcnow()), groupId))

    def _endTimer(self):
        with self.conn:
            self.conn.execute('''UPDATE timers SET end = ?
                WHERE name LIKE ? AND end IS NULL''',
                (self._roundTime(datetime.utcnow()), self.name))

    def _showTimer(self):
        query = 'SELECT id, name, note, start, end FROM timers'
        where = []
        params = list()
        if not self.showAll:
            where.append('end IS NULL')

        if (self.name != '*'):
            where.append('name LIKE ?')
            params.append(self.name)

        if (where):
            query = query + ' WHERE ' + ' AND '.join(where)

        for row in self.conn.execute(query, params):
            formattedStart = formatTime(row['start'])
            end = row['end'] if row['end'] else datetime.utcnow()
            duration = self._roundTime(end - row['start'])
            print('%s(%d): %s %s %s'
                % (row['name'], row['id'], formattedStart, duration,
                    row['note'] if row['note'] else ''))

    def _editTimer(self):
        with self.conn:
            self.conn.execute('''UPDATE timers SET note = ?,
                start = ?, end = ? WHERE name LIKE ?''',
                (self.note, self.start, self.end, self.name))

    def _assignGroup(self):
        with self.conn:
            self.conn.execute('''UPDATE groups SET project_id = ?,
                ticket_id = ? WHERE name LIKE ?''',
                (self.project, self.ticket, self.name))

    def _findProject(self):
        self._syncProjects()
        if (self.type == 'projects'):
            # Do stuff for projects here
            pass
        elif (self.type == 'tickets'):
            # Do stuff for tickets here
            pass
        else:
            # Do stuff for searching both here
            pass

    def _noOp(self):
        print('There is no defined operation for the command %s.' % self.op)

    def _initDB(self):
        needsSchemaUpgrade = not path.exists(self.dataPath)

        self.conn = sqlite3.connect(self.dataPath,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row

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
            with open(self.scriptPath, 'rt') as f:
                schema = f.read()
            self.conn.executescript(schema)

    def _syncProjects(self):
        if (self.url == None or self.token == None or self.cacheFunction == None):
            raise RuntimeError('Either url, token, or accountType is NULL, check config file')

        lifetime = timedelta(hours=self.cacheLifetime)

        # print('Last Synced: ', formatTime(self.lastSynced),
        #    ', time elapsed: ', delta,
        #    ', configured lifetime: ', lifetime)

        if (not self.lastSynced or datetime.utcnow() - self.lastSynced > lifetime):
            self.cacheFunction()

        self.lastSync = datetime.utcnow()

    def _syncProjectsAC(self):
        with self.conn:
            req = ACRequest('projects', ac_url=self.url, api_key=self.token)
            for project in req.execute():
                # print(project)
                self.conn.execute('''
                    INSERT OR REPLACE INTO projects(id, name) VALUES (?, ?)
                ''', (project['id'], project['name']))

                req = ACRequest('projects', item_id=project['id'],
                    subcommand='tickets', ac_url=self.url, api_key=self.token)

                for ticket in req.execute():
                    # print(ticket)
                    self.conn.execute('''
                        INSERT OR REPLACE INTO tickets(id, project_id, name)
                            VALUES (?, ?, ?)
                    ''', (ticket['ticket_id'], project['id'], ticket['name']))

    def _syncProjectsFB(self):
        pass

    def _findGroupId(self, group):
        groupId = -1
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

    parser_show = subparsers.add_parser('show', help='List all running timers')
    parser_show.add_argument('name', nargs='?', default='*', help='Specify a timer to show details about')
    parser_show.add_argument('-a', '--all', dest='showAll', action='store_true', default=False,
        help='Show all timers.  The default behaviour is to show only running timers')

    parser_edit = subparsers.add_parser('edit', help='Edit a stopped timer')
    parser_edit.add_argument('name', help='Specify a timer to show details about')
    parser_edit.add_argument('-n', '--note', help='Note to set for this timer')
    parser_edit.add_argument('-s', '--start', type=parseTime, help='Start date to set for this timer')
    parser_edit.add_argument('-e', '--end', type=parseTime, help='Duration to set for this timer')
    parser_edit.add_argument('-g', '--group', help='Group name to set this timer to')

    parser_assign = subparsers.add_parser('assign', help='Assign a group to a ticket')
    parser_assign.add_argument('name', help='Group to assign a ticket')
    parser_assign.add_argument('project', help='Project id to assign group to')
    parser_assign.add_argument('ticket', help='Ticket id to assign group to')

    parser_projects = subparsers.add_parser('find', help='Show details about projects')
    parser_projects.add_argument('name', help='Name to search for')
    parser_projects.add_argument('-t', '--type', default='*', choices=['*', 'ticket', 'project'],
        help='If we should look for projects, tickets or both (defaults to both)')

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
        'cacheLifetime': userConfig['account']['cache_lifetime'],
    })

    QTimer(config).run()

    return 0

if __name__ == '__main__':
    exit(main())
