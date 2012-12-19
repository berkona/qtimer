#! /usr/bin/env python

# import freshbooks
import argparse
import sqlite3
import json
import tz

from activecollab.library import ACRequest
from datetime import datetime, timedelta
from os import path, makedirs

DB_VERSION = 3
CONFIG_NAME = 'qtimer.json'
DATA_NAME = 'timers v%d.db' % DB_VERSION


class PyTimer:
    def __init__(self, config):
        for n, v in vars(config).items():
            setattr(self, n, v)

        scriptRoot = path.expanduser('~/.qtimer')
        if not path.exists(scriptRoot):
            makedirs(scriptRoot)

        self.dataPath = path.join(scriptRoot, DATA_NAME)
        self.configPath = path.join(scriptRoot, CONFIG_NAME)

        self.token = None
        self.url = None

        if not path.exists(self.configPath):
            return

        with open(self.configPath, 'r') as f:
            userConfig = json.load(f)
            self.token = userConfig['account']['token']
            self.url = userConfig['account']['url']

    def run(self):
        self.conn = sqlite3.connect(self.dataPath,
            detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        try:
            self._initDB()
            return {
                'start': self._startTimer,
                'end': self._endTimer,
                'show': self._showTimer,
                'edit': self._editTimer,
                'assign': self._assignGroup,
                'projects': self._listProjects
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        with self.conn:
            groupId = self._findGroupId(self.group) if self.group else -1

            # If row is not None and groupId is still -1, we need to create this group
            if (self.group and groupId == -1):
                self.conn.execute('''INSERT INTO groups(name)
                        VALUES (?)''', self.group)
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
        query = '''SELECT id, name, note, start, end FROM timers'''
        params = list()
        if (self.name == 'all'):
            query += ' WHERE end IS NULL'
        else:
            query += ' WHERE name LIKE ?'
            params.append(self.name)

        for row in self.conn.execute(query, params):
            utc = row['start'].replace(tzinfo=tz.UTC)
            formattedStart = utc.astimezone(tz.Local).strftime('%x %H:%M')
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

    def _listProjects(self):
        if self.name == 'all':
            req = ACRequest('projects', api_key=self.token, ac_url=self.url)
            for url in req.execute():
                print(type(url), '=>', url)

    def _noOp(self):
        print('There is no defined operation for the command %s.' % self.op)

    def _initDB(self):
        with self.conn:
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS timers
                (id integer PRIMARY KEY AUTOINCREMENT, group_id integer,
                name text NOT NULL, note text, start timestamp, end timestamp)
            ''')
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS groups
                (id integer PRIMARY KEY AUTOINCREMENT, name text NOT NULL,
                 project_id integer, ticket_id integer)
            ''')

    def _findGroupId(self, group):
        groupId = -1
        curs = self.conn.execute('''SELECT id FROM groups
                WHERE name LIKE ?''', group)
        row = curs.fetchone()
        if (row):
            groupId = row[0]
        return groupId

    def _roundTime(dt=None, roundTo=60):
        if dt == None:
            dt = datetime.utcnow()

        seconds = (dt - dt.min).seconds
        # // is a floor division not a comment on the following line
        rounding = (seconds + roundTo / 2) // roundTo * roundTo
        ms = dt.microseconds if hasattr(dt, 'microseconds') else 0
        return dt + timedelta(0, rounding - seconds, -ms)


def parseTime(dateStr):
    return datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Available commands', dest='op',)

    parser_start = subparsers.add_parser('start', help='Start a timer')
    parser_start.add_argument('name', help='Name of the timer to be created')
    parser_start.add_argument('-n', '--note', help='An optional note for this timer')
    parser_start.add_argument('-g', '--group', help='An optional group name')

    parser_end = subparsers.add_parser('end', help='End a currently running timer')
    parser_end.add_argument('name', help='Name of the timer to be stopped')

    parser_show = subparsers.add_parser('show', help='List all running timers')
    parser_show.add_argument('name', nargs='?', default='all',
        help='Specify a timer to show details about')

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

    parser_projects = subparsers.add_parser('projects',
        help='Show details about projects')
    parser_projects.add_argument('name', nargs='?', default='all',
        help='Specify a timer to show details about')

    config = parser.parse_args()

    # Check that we have a task to do
    if not config.op:
        parser.print_help()
        return -1

    PyTimer(config).run()

    return 0

if __name__ == '__main__':
    exit(main())
