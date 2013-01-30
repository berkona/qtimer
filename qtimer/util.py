import logging

from contextlib import contextmanager
from datetime import datetime

from qtimer.lib import tz
from qtimer.env import DATA_DIR


def filter_module_prototypes(prototypeName):
	return not ()

def expand_sql_url(url):
	return url.replace('DATA_DIR', DATA_DIR)


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
		logging.getLogger(__name__).warn('Rolling back session %s because of %s.'\
			% (repr(session), repr(e)))
		session.rollback()
		raise
