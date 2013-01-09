#! /usr/bin/env python3

# System imports
from datetime import datetime, timedelta
from os import path, makedirs, listdir
from contextlib import contextmanager
from importlib import import_module

import configparser
import argparse
import logging

import logging.config

# SQLALchemy
from alembic.config import Config
import sqlalchemy as sa
import alembic.command

# Custom
from qtimer.util import smart_truncate, autocommit, expand_sql_url
from qtimer.model import Ticket, Project, PersistentVar
from qtimer.lib import terminalsize
from qtimer.strings import strings

PLUGIN_MOD = 'plugins.%s.plugin'
COMMANDS_MOD = 'commands.%s'

SCRIPT_ROOT = path.dirname(path.realpath(__file__))

# This is what we use for writing to the database
SQLSession = sa.orm.sessionmaker()


class QTimerProgram:

    # We use getter properties to offset resource creation until we need it
    @property
    def commands(self):
        if hasattr(self, '_commands'):
            return self._commands

        self._commands = {}
        commandPath = path.join(SCRIPT_ROOT, 'commands')
        files = (path.splitext(item)[0] for item in listdir(commandPath)
            if not (item == '__init__.py' or item == 'command.py')
            and path.isfile(path.join(commandPath, item)))

        for f in files:
            self.importCommand(f)

        return self._commands

    @property
    def lastSynced(self):
        if hasattr(self, '_lastSynced'):
            return self._lastSynced
        q = self.session.query(PersistentVar).filter(PersistentVar.name.like('lastSynced'))
        try:
            self._lastSynced = q.one().value
            return self._lastSynced
        except:
            pass

    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session

        # This also has the side-effect of initializing the database and logging
        alembic_ini = Config(path.join(SCRIPT_ROOT, 'alembic.ini'))

        if self.config.verbose:
            logging.config.fileConfig(path.join(SCRIPT_ROOT, 'logging.verbose.ini'))
        else:
            logging.config.fileConfig(path.join(SCRIPT_ROOT, 'logging.default.ini'))

        alembic.command.upgrade(alembic_ini, "head")

        self.engine = sa.create_engine(
            expand_sql_url(alembic_ini.get_main_option("sqlalchemy.url")),
            encoding="utf-8", echo=False
        )

        SQLSession.configure(bind=self.engine)

        self._session = SQLSession()
        return self._session

    @property
    def plugin(self):
        if hasattr(self, '_plugin'):
            return self._plugin

        if not (self.config.url and self.config.token and self.config.accountType):
            raise RuntimeError(strings['bad_config'])

        try:
            mod = import_module(PLUGIN_MOD % self.config.accountType)
            self._plugin = mod.load_qtimer_plugin(self.config.url, self.config.token)
            return self._plugin
        except ImportError:
            raise RuntimeError(strings['no_plugin_found'] % self.config.accountType)

    @property
    def parser(self):
        if hasattr(self, '_parser'):
            return self._parser

        parser = argparse.ArgumentParser()

        subparsers = parser.add_subparsers(title=strings['command_title'], dest='op')

        for identifier, command in self.commands.items():
            if hasattr(command, 'COMMAND_HELP'):
                subparser = subparsers.add_parser(identifier, help=command.COMMAND_HELP)
            else:
                subparser = subparsers.add_parser(identifier)
            command.addArguments(subparser)

        self._parser = parser
        return self._parser

    @property
    def config(self):
        if hasattr(self, '_config'):
            return self._config

        configRoot = path.expanduser('~/.qtimer')
        if not path.exists(configRoot):
            makedirs(configRoot)

        configPath = path.join(configRoot, 'qtimer.ini')

        userConfig = configparser.ConfigParser()
        with open(path.join(SCRIPT_ROOT, 'default.ini')) as defaultFile:
            userConfig.readfp(defaultFile)

        if not path.exists(configPath):
            raise RuntimeError(strings['no_config'])

        userConfig.read(configPath)

        class Config(object):
            pass

        self._config = Config()

        # userConfig fields
        self._config.configRoot = configRoot
        self._config.configPath = configPath
        self._config.accountType = userConfig['account']['type']
        self._config.url = userConfig['account']['url']
        self._config.token = userConfig['account']['token']
        self._config.cacheLifetime = int(userConfig['account']['cache_lifetime'])
        self._config.rounding = int(userConfig['timers']['rounding'])

        self._config.verbose = userConfig['debug']['verbose'].lower() == 'true'

        return self._config

    def parseArgs(self, argsOverride=None):
        args = self.parser.parse_args(argsOverride)
        if not args.op:
            self.parser.print_help()
            raise RuntimeError(strings['no_op'])

        return args

    def importCommand(self, f):
        # Predict the class name to be the TitleCase of the script mod
        className = f.title().replace('_', '')
        mod = import_module(COMMANDS_MOD % f)
        command = getattr(mod, className)()

        if not hasattr(command, 'COMMAND_IDENTIFIER'):
            raise RuntimeError('Command %s must declare an ID' % (COMMANDS_MOD % f))

        self._commands[command.COMMAND_IDENTIFIER] = command

    def executeCommand(self, args):
        command = self.commands.get(args.op, None)
        if not command:
            raise RuntimeError('No command found matching ' + args.op)
        return command.runCommand(args, self)

    def outputRows(self, rows=[], header=(), weights=()):
        if not weights:
            lenHeader = len(header)
            weights = tuple([(1 / lenHeader) for i in range(lenHeader)])

        totalWeight = sum(weights)
        if (totalWeight > 1 or totalWeight < 0.99):
            raise RuntimeError('The sum of all weights must be about 1, totalWeight: %f' % totalWeight)

        totalWidth = terminalsize.get_terminal_size()[0]
        widths = []
        formatStr = ''
        for weight in weights:
            width = int(totalWidth * weight)
            formatStr += '%-' + str(width) + 's'
            widths.append(width)

        print(formatStr % header)
        print('-' * totalWidth)
        for row in rows:
            items = []
            for i, item in enumerate(row):
                if isinstance(item, str) and len(item) > widths[i]:
                    item = smart_truncate(item, widths[i])
                items.append(item)
            print(formatStr % tuple(items))

    def syncConditionally(self):
        lifetime = timedelta(minutes=self.config.cacheLifetime)

        if (not self.lastSynced
            or datetime.utcnow() - self.lastSynced > lifetime):
            self.sync()

    def sync(self):
        logging.getLogger('qtimer').info(strings['old_data'] % (self.config.accountType, self.config.url))

        with autocommit(self.session) as session:
            project_ids = []
            ticket_ids = []

            projects = self.plugin.listProjects()
            for project in projects:
                project_ids.append(project.id)
                session.merge(project)
                tickets = self.plugin.listTickets(project.id)
                for ticket in tickets:
                    ticket_ids.append(ticket.id)
                    session.merge(ticket)

            session.query(Project).filter(~Project.id.in_(project_ids)).delete('fetch')
            session.query(Ticket).filter(~Ticket.id.in_(ticket_ids)).delete('fetch')

            lastSynced = PersistentVar(name='internal.lastSynced', value=datetime.utcnow())
            session.merge(lastSynced)

    def roundTime(self, dt):
        roundTo = self.config.rounding
        seconds = (dt - dt.min).seconds
        # // is a floor division not a comment on the following line
        rounding = (seconds + roundTo / 2) // roundTo * roundTo
        ms = dt.microseconds if hasattr(dt, 'microseconds') else 0
        ret = dt + timedelta(0, rounding - seconds, -ms)
        return ret

    def close(self):
        self.session.close()

@contextmanager
def create_qtimer():
    qtimer = QTimerProgram()
    try:
        yield qtimer
    finally:
        qtimer.close()
        SQLSession.close_all()


def main():
    with create_qtimer() as qtimer:
        args = qtimer.parseArgs()
        qtimer.executeCommand(args)

if __name__ == '__main__':
    exit(main())
