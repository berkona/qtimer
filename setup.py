from distutils.core import setup

setup(
	name='QTimer',
	version='0.1.0',
	author='Jon "Berkona" Monroe',
	author_email='solipsis.dev@gmail.com',
	packages=[
		'qtimer', 'qtimerui', 
		'qtimer.lib', 'qtimer.commands', 
		'qtimer.plugins', 'qtimer.schema',
		'qtimer.schema.versions'
	],
	scripts=['bin/qtimer', 'bin/qtimer-ui'],
	license='LICENSE.txt',
	description='A small timer program that integrates with various project management solutions',
	long_description=open('README.md').read(),
	install_requires=[
		'sqlalchemy >= 0.7.9',
		'alembic >= 0.4.1',
		'appdirs >= 1.2.0'
	],
)
