from qtimer.plugins.prototype import PluginPrototype


# Yes, magic methods suck, but this makes it easier to use classes
def load_qtimer_plugin(url=None, token=None):
	return OfflinePlugin()


class OfflinePlugin(PluginPrototype):
	def listProjects(self):
		"""
			Return a list of dictionary objects representing a project.  Each project
			should at the least have a unique id and a name.  Names aren't required
			to be unique, but overlapping names will result in user frustration
			because all results of that name will be shown
		"""
		return []

	def listTickets(self, projectId=-1):
		"""
			Return a list of dictionary objects representing tickets in a given
			project.
		"""
		return []

	def postTimer(self, projectId=-1, ticketId=-1, data=None):
		pass
