from datetime import datetime

from qtimer.commands.command import Command
from qtimer.model import Timer, Session
from qtimer.strings import strings
from qtimer.util import autocommit


class EndTimer(Command):

    COMMAND_IDENTIFIER = 'end'
    COMMAND_HELP = strings['command_end']

    def addArguments(self, parser):
        parser.add_argument('name', help=strings['command_name'])

    def runCommand(self, args, program):
        with autocommit(program.session) as session:

            values = {
                Session.end: program.roundTime(datetime.utcnow())
            }

            query = session.query(Timer).filter(Timer.name.like('%' + args.name + '%'))
            for timer in query:
                session.query(Session).filter(Session.timer_id == timer.id)\
                    .filter(Session.end == None).update(values)

        args = program.parseArgs(['find', 'timers', '-n', args.name])
        return program.executeCommand(args)
