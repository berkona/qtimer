#! /usr/bin/env python

import freshbooks
import sqlite3
import argparse
import json

from activecollab.library import ACRequest
from datetime import datetime

from os import path

CONFIG_NAME = 'config.json'
DATA_NAME = 'timers.db'

class PyTimer:
    def __init__(self, config):
        for n, v in vars(config).items():
            setattr(self, n, v)

        scriptRoot = path.dirname(path.realpath(__file__))
        self.dataPath = path.join(scriptRoot, DATA_NAME)

    def run(self):
        self.conn = sqlite3.connect(self.dataPath)
        self.conn.row_factory = sqlite3.Row
        try:
            self._initDB()
            retVal = {
                'start': self._startTimer,
                'end': self._endTimer,
                'status': self._getTimerStatus,
            }.get(self.op, self._noOp)()
        finally:
            self.conn.close()

    def _startTimer(self):
        with self.conn:
            self.conn.execute('INSERT INTO timers(name, note, start) VALUES (?, ?, ?) ', 
                (self.name, self.note, datetime.utcnow()))

    def _endTimer(self):
        with self.conn:
            self.conn.execute('UPDATE timers SET end = ? WHERE name LIKE ? AND end IS NULL',
                (datetime.utcnow(), self.name))

    def _getTimerStatus(self):
        query = 'SELECT name, note, start, end FROM timers'
        params = list()
        if (self.name == 'all'):
            query += ' WHERE end IS NULL'
        else:
            query += ' WHERE name LIKE ?'
            params.append(self.name)

        i = 0
        for row in self.conn.execute(query, params):
            timer = []
            for val in row:
                timer.append(str(val))
            print(i, ': ', ', '.join(timer))
            i += 1

    def _noOp(self):
        print('There is no defined operation for the command %s.' % self.op)

    def _initDB(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS timers 
                (name text PRIMARY KEY NOT NULL, note text, start date, end date) ''')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Available commands', dest='op',)

    parser_start = subparsers.add_parser('start', help='Start a timer')
    parser_start.add_argument('name', help='Name of the timer to be created')
    parser_start.add_argument('-n', '--note', help='An optional note for this timer')

    parser_end = subparsers.add_parser('end', help='End a currently running timer')
    parser_end.add_argument('name', help='Name of the timer to be stopped')
    
    parser_status = subparsers.add_parser('status', help='List all running timers')
    parser_status.add_argument('name', nargs='?', default='all', 
        help='Specify a timer to show details about')

    config = parser.parse_args()

    # Check that we have a task to do
    if not hasattr(config, 'op'):
        parser.print_help()
        return -1

    PyTimer(config).run()

    return 0

if __name__ == '__main__':
    exit(main())