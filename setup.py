from distutils.core import setup
from distutils.dir_util import copy_tree

from os import makedirs, path

from qtimer.env import DATA_DIR, SCRIPT_ROOT

setup(
	name='qTimer',
	version='0.1.0',
	author='Jon "Berkona" Monroe',
	author_email='solipsis.dev@gmail.com',
	packages=[
		'qtimer', 'qtimer.lib', 'qtimer.commands',
		'qtimer.plugins', 'qtimer.schema',
		'qtimer.schema.versions',
	],
	scripts=['bin/qtimer', ],
	license='LICENSE.txt',
	description='A small timer program that integrates with various project management solutions',
	long_description=open('README.md').read(),
	install_requires=[
		'sqlalchemy >= 0.7.9',
		'alembic >= 0.4.1',
		'appdirs >= 1.2.0'
	],
)

print("Copying schema information to user data directory")

schemaDest = path.join(DATA_DIR, 'schema')

if not path.exists(schemaDest):
	makedirs(schemaDest)

copy_tree(path.join(SCRIPT_ROOT, 'schema'), schemaDest)
