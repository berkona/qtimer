class PluginPrototype:
	def listProjects(self):
		"""
			Return a list of dictionary objects representing a project.  Each project
			should at the least have a unique id and a name.  Names aren't required
			to be unique, but overlapping names will result in user frustration
			because all results of that name will be shown
		"""
		raise PluginError('You must implement this method')

	def listTickets(self, projectId = -1):
		"""
			Return a list of dictionary objects representing tickets in a given
			project.
		"""
		raise PluginError('You must implement this method')

	def postTimer(self, projectId = -1, ticketId = -1, data = None):
		raise PluginError('You must implement this method')

class PluginError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
