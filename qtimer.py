#! /usr/bin/env python

# import freshbooks
import sqlite3
import argparse
import tz

# import json

# from activecollab.library import ACRequest
from datetime import datetime, timedelta
from os import path

DB_VERSION = 2
CONFIG_NAME = 'qtimer.json'
DATA_NAME = 'timers v%d.db' % DB_VERSION


class PyTimer:
    def __init__(self, config):
        for n, v in vars(config).items():
            setattr(self, n, v)

        scriptRoot = path.dirname(path.realpath(__file__))
        self.dataPath = path.join(scriptRoot, DATA_NAME)

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
                'edit': self._editTimer
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        with self.conn:
            self.conn.execute('INSERT INTO timers(name, note, start) VALUES (?, ?, ?) ',
                (self.name, self.note, self._roundTime(datetime.utcnow())))

    def _endTimer(self):
        with self.conn:
            self.conn.execute('UPDATE timers SET end = ? WHERE name LIKE ? AND end IS NULL',
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
            formattedStart = row['start'].replace(tzinfo=tz.UTC).astimezone(tz.Local).strftime('%x %H:%M')
            end = row['end'] if row['end'] else datetime.utcnow()
            duration = self._roundTime(end - row['start'])
            print('%s(%d): %s %s %s'
                % (row['name'], row['id'], formattedStart, duration,
                    row['note'] if row['note'] else ''))

    def _editTimer(self):
        with self.conn:
            self.conn.execute('UPDATE timers SET note = ?, start = ?, end = ? WHERE name LIKE ?',
                (self.note, self.start, self.end, self.name))

    def _noOp(self):
        print('There is no defined operation for the command %s.' % self.op)

    def _initDB(self):
        with self.conn:
            self.conn.execute(
            '''CREATE TABLE IF NOT EXISTS timers
                (id integer PRIMARY KEY AUTOINCREMENT, name text NOT NULL,
                    note text, start timestamp, end timestamp) ''')

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

    config = parser.parse_args()

    # Check that we have a task to do
    if not config.op:
        parser.print_help()
        return -1

    PyTimer(config).run()

    return 0

if __name__ == '__main__':
    exit(main())
