import logging

from contextlib import contextmanager
from datetime import datetime
from os import path
from lib import tz


def expand_sql_url(url):
    try:
        idx = url.index('~')
        url = url[:idx] + path.expanduser(url[idx:])
    except ValueError:
        pass
    return url


def smart_truncate(content, length=100, suffix='...'):
    length = length - len(suffix)
    if len(content) <= length:
        return content
    else:
        return content[:length].rsplit(' ', 1)[0] + suffix


def parse_time(dateStr):
    return datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


def format_time(datetime):
    utc = datetime.replace(tzinfo=tz.UTC)
    return utc.astimezone(tz.Local).strftime('%x %H:%M')


@contextmanager
def autocommit(session):
    try:
        yield session
        session.commit()
    except BaseException as e:
        logging.getLogger('qtimer').warn('Rolling back session %s because of %s.' % (repr(session), repr(e)))
        session.rollback()
        raise
