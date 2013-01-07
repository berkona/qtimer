# System imports
from datetime import datetime, timedelta

# SQLAlchemy imports
from sqlalchemy import Column, Integer, Boolean, Unicode, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship

# Base to store our metadata
Base = declarative_base()

BILLABLE_STATUSES = {
	'billable': 0,
	'non-billable': 1,
}


class BaseMixin(object):
	@declared_attr
	def __tablename__(cls):
		return '%ss' % cls.__name__.lower()

	# A unique id for this object
	id = Column(Integer, primary_key=True)


class NamedMixin(object):
	# A name for this object (non-unique)
	name = Column(Unicode(256), nullable=False)


class ReadSyncMixin(object):
	# Records when an object was last synced with the remote (Read-only objects)
	synced_date = Column(DateTime, nullable=False, server_default=func.now())


class Project(BaseMixin, NamedMixin, ReadSyncMixin, Base):
	# Defines a one-to-many relationship between Project and Ticket
	tickets = relationship('Ticket', backref='project', passive_updates=False)


class Ticket(BaseMixin, NamedMixin, ReadSyncMixin, Base):
	# An id which is unique only to this ticket's project, used for remote requests
	ticket_id = Column(Integer, nullable=False)

	# Defines a many-to-one relationship between Timer and Ticket
	timers = relationship('Timer', backref='ticket', passive_updates=False)

	# Defines a one-to-many relationship between Project and Ticket
	project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)


class Session(BaseMixin, Base):
	start = Column(DateTime, nullable=False)
	end = Column(DateTime, nullable=True, default=None)

	# Defines a one-to-many relationship between Timer and Session
	timer_id = Column(Integer, ForeignKey('timers.id'), nullable=False)


class Timer(BaseMixin, NamedMixin, Base):
	posted = Column(Boolean, nullable=False, default=False)
	billable_status = Column(Integer, nullable=True, default=None)

	# Defines a many-to-one relationship between Timer and Ticket
	ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=True)

	# Defines a one-to-many relationship between Timer and Session
	sessions = relationship('Session', order_by=Session.start, passive_updates=False)

	@property
	def start(self):
		return self.sessions[0].start if self.sessions else None

	@property
	def duration(self):
		duration = timedelta()
		for session in self.sessions:
			end = session.end if session.end else datetime.utcnow()
			duration += (end - session.start)
		return duration


