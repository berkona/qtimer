from distutils.core import setup

setup(
	name='qTimer',
	version='0.1.1',
	author='Jon "Berkona" Monroe',
	author_email='solipsis.dev@gmail.com',
	url='https://github.com/berkona/qtimer',
	packages=[
		'qtimer', 'qtimer.lib',
		'qtimer.commands', 'qtimer.plugins',
	],
	package_data={'qtimer':
		['schema/*.py', 'schema/versions/*.py', 'default.ini'],
	},
	scripts=['bin/qtimer', ],
	license='LICENSE.txt',
	description='A small timer program that integrates with various project management solutions',
	long_description=open('README.txt').read(),
	install_requires=[
		'sqlalchemy >= 0.7.9',
		'alembic >= 0.4.1',
		'appdirs >= 1.2.0'
	],
)
