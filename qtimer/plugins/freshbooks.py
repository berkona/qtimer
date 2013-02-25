# This is the real library we use
# we're just 'talking' like qTimer now
from refreshbooks import api

from qtimer.plugins.prototype import PluginPrototype, PluginError
from qtimer.model import Project, Ticket
from qtimer.env import APP_NAME, VERSION


# Yes, magic methods suck, but this makes it easier to use classes
def load_qtimer_plugin(url=None, token=None):
	return FreshBooksPlugin(url, token)


def FreshBooksPlugin(PluginPrototype):
	def __init__(self, url, token):
		self.client = api.TokenClient(
			url,
			token,
			user_agent='%s/%s' % (APP_NAME, VERSION)
		)

	def listProjects(self):
		response = self.client.project.list()

		# Be nice and give them a filter object
		makeProject = lambda item: Project(
			id=item.project_id, name=item.name
		)
		return filter(makeProject, response.projects.project)

	def listTickets(self, projectId=-1):
		if (projectId == -1):
			raise PluginError('Invalid project id')
		response = self.client.tasks.list(dict(project_id=projectId))

		makeTicket = lambda task: Ticket(
			id=task.task_id, name=task.name,
			ticket_id=task.task_id, project_id=projectId
		)

		return filter(makeTicket, response.tasks.task)

	def postTimer(self, projectId=-1, ticketId=-1, data=None):
		# TODO
		pass
