import logging

from contextlib import contextmanager
from datetime import datetime

from qtimer.lib import tz
import qtimer.env


def filter_module_prototypes(prototypeName):
	return not ()


def expand_sql_url(url):
	return expand_env_var('DATA_DIR', url)


def expand_env_var(varname, string):
	if not hasattr(qtimer.env, varname):
		raise RuntimeError('Environment does not have given variable')
	varval = getattr(qtimer.env, varname)
	return string.replace(varname, varval)


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
