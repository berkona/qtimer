import alembic.config as config
import configparser
from os import path

from qtimer.strings import strings


class Section(object):
	pass


class Config(config.Config):
	def __init__(self, configPath, defaultsPath=None):
		super(Config, self).__init__(defaultsPath)

		self.parser = configparser.ConfigParser()
		with open(defaultsPath) as defaultFile:
			self.parser.readfp(defaultFile)

		if not path.exists(configPath):
			raise RuntimeError(strings['no_config'])

		self.parser.read(configPath)

		isLoggerSection = lambda section: not (section.startswith('logger')
			or section.startswith('handler') or section.startswith('formatter'))

		sections = filter(isLoggerSection, self.parser.sections())
		for section in sections:
			setattr(self, section, Section())
			mySection = getattr(self, section)
			for option in self.parser.options(section):
				attr_name = option.replace('.', '_')
				value = self.parser.get(section, option)
				setattr(mySection, attr_name, value)

	def get_section(self, name):
		return dict(self.parser.items(name))

	def get_section_option(self, section, name, default=None):
		if not self.parser.has_section(section):
			raise RuntimeError(
				'No config file %r found, or file has no "[%s]" section'
				% (self.parser, section))

		if self.parser.has_option(section, name):
			return self.parser.get(section, name)
		else:
			return default
