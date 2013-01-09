from distutils.core import setup

setup(
	name='QTimer',
	version='0.1.0',
	author='Jon "Berkona" Monroe',
	author_email='solipsis.dev@gmail.com',
	packages=['qtimer'],
	scripts=['bin/qtimer', 'bin/qtimer-gui'],
	license='LICENSE.txt',
	description='A small timer program that integrates with various project management solutions',
	long_description=open('README.txt').read(),
	install_requires=[
		"sqlalchemy >= 0.7.9"
		"alembic >= 0.4.1"
	],
)
