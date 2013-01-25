# System imports
from datetime import datetime, timedelta

# SQLAlchemy imports
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql.expression import *
from sqlalchemy.orm import relationship


# Base to store our metadata
Base = declarative_base()

BILLABLE_STATUSES = {
	'billable': 0,
	'non-billable': 1,
}

STATUS_ACTIVE = 'active'
STATUS_IDLE = 'idle'
STATUS_POSTED = 'posted'


class BaseMixin(object):
	@declared_attr
	def __tablename__(cls):
		return 'qtimer_%ss' % cls.__name__.lower()

	# A unique id for this object
	id = Column(Integer, primary_key=True)


class NamedMixin(object):
	# A name for this object (non-unique)
	name = Column(Unicode(256), nullable=False)


class PersistentVar(Base):
	@declared_attr
	def __tablename__(cls):
		return 'qtimer_%ss' % cls.__name__.lower()

	name = Column(Unicode(256), nullable=False, primary_key=True)
	value = Column(PickleType, nullable=False)


class Project(BaseMixin, NamedMixin, Base):
	# Defines a one-to-many relationship between Project and Ticket
	tickets = relationship('Ticket',  order_by='Ticket.name', backref='project', passive_updates=False)


class Ticket(BaseMixin, NamedMixin, Base):
	# An id which is unique only to this ticket's project, used for remote requests
	ticket_id = Column(Integer, nullable=False, index=True)

	# Defines a many-to-one relationship between Timer and Ticket
	timers = relationship('Timer', backref='ticket', passive_updates=False)

	# Defines a one-to-many relationship between Project and Ticket
	project_id = Column(Integer, ForeignKey('qtimer_projects.id'), nullable=False)


class Timer(BaseMixin, NamedMixin, Base):
	posted = Column(Boolean, nullable=False, default=False)
	billable_status = Column(Integer, nullable=True, default=None)

	# Defines a many-to-one relationship between Timer and Ticket
	ticket_id = Column(Integer, ForeignKey('qtimer_tickets.id'), nullable=True)

	# Defines a one-to-many relationship between Timer and Session
	sessions = relationship('Session', order_by='Session.start', passive_updates=False)

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

	@property
	def status(self):
		if self.posted:
			return STATUS_POSTED
		for session in self.sessions:
			if not session.end == None:
				continue
			return STATUS_ACTIVE
		return STATUS_IDLE


class Session(BaseMixin, Base):
	start = Column(DateTime, nullable=False, index=True)
	end = Column(DateTime, nullable=True, default=None, index=True)

	# Defines a one-to-many relationship between Timer and Session
	timer_id = Column(Integer, ForeignKey('qtimer_timers.id'), nullable=False)
