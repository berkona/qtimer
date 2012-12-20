# These are the 'top level' commands available
AC_COMMANDS = ('projects', 'people', 'calendar')
AC_SUBCOMMAND = ('tickets', 'discussions', 'milestones', 'files',
    'pages', 'time', 'comment')

# The following is a list of sub elements of the main
# command XML which is returned
AC_COMMAND_ELEMENT = {
    'projects': 'project',
    'people': 'company',
    'discussions': 'topic',
    'tickets': 'ticket',
    'milestones': 'milestone',
    'time': 'time_record',
    'page': 'category',
    'comments': 'comment',
    'files': 'file',
}

# These fields are common throughout XML responses so we
# grab these for all items as a good start
AC_BASE_FIELDS = ('id', 'name', 'permalink')
AC_SUB_FIELDS = {
    'tickets': ('ticket_id',)
}

# Used in printing output
AC_FIELD_SEP = ': '