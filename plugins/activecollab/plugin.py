from plugins.prototype import PluginPrototype, PluginError
from plugins.activecollab.library import ACRequest

# Yes, magic methods suck, but this makes it easier to use classes
def load_qtimer_plugin(url = None, token = None):
	return ActiveCollabPlugin(url, token)

class ActiveCollabPlugin(PluginPrototype):

	def __init__(self, url, token):
		PluginPrototype()
		self.url = url
		self.token = token

	def listProjects(self):
		req = ACRequest('projects', ac_url=self.url, api_key=self.token)
		return req.execute()

	def listTickets(self, projectId = -1):
		if (projectId == -1):
			raise PluginError('Invalid project id')

		req = ACRequest('projects', item_id=projectId, subcommand='tickets',
			ac_url=self.url, api_key=self.token)
		return req.execute()

	def postTimer(self, projectId = -1, ticketId = -1, data = None):
		if (projectId == -1):
			raise PluginError('Invalid project id')

		if (ticketId == -1):
			raise PluginError('Invalid ticket id')

		req = ACRequest('projects', item_id=projectId, subcommand='time/add',
			data=data, ac_url=self.url, api_key=self.token)
		return req.execute()
