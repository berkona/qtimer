strings = {
    'command_title': 'Available commands',
    'command_name': 'Name of object to select',
    'command_start': 'Create a new timer and start it',
    'command_start_note': 'An optional note for this timer',
    'command_start_group': 'An optional group name',
    'command_end': 'End a currently running timer',
    'command_edit': 'Edit a stopped timer',
    'command_edit_note': 'Note to set for this timer',
    'command_edit_start': 'Start date to set for this timer',
    'command_edit_end': 'Duration to set for this timer',
    'command_edit_group': 'Group name to set this timer to',
    'command_assign': 'Assign a group to a ticket',
    'command_assign_project': 'Project id to assign group to',
    'command_assign_ticket': 'Ticket id to assign group to',
    'command_show': 'List all running timers',
    'command_find': 'Show details about objects in database',
    'command_find_name': 'Specify a timer to show details about',
    'command_find_id': 'Find a specific id',
    'command_find_group': 'Show timers from a specific group',
    'command_find_project': 'Find tickets in a project',
    'command_post': 'Post a timer to the configured remote source',
    'command_refresh': 'Refresh configured remote source immediately',

    'new_db': 'Creating new database for schema version: %d',
    'old_data': 'Reloading cache from configured remote source: %s://%s',
    'bad_config': 'Either config file is invalid or does not exist',
    'no_op': 'There is no defined operation for this input',
    'no_config': 'You must define a config file with an accountType, url and authentication token',
    'no_plugin_found': 'No plugin found matching accountType %s',
    'debug_query': 'SQLite Query used:',

    'timer_header': (
        'ID',
        'Name',
        'Group',
        'Start',
        'Duration',
        'Note',
    ),

    'groups_header': (
        'ID',
        'Name',
        'PID',
        'Project Name',
        'TID',
        'Ticket Name',
    ),

    'projects_header': (
        'ID',
        'Name',
    ),

    'tickets_header': (
        'PID',
        'Project Name',
        'TID',
        'Ticket Name',
    ),
}
