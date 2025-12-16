"""
Project State Management
"""
PROJECT_STATE = {
    'plan': {},
    'current_file': None,
    'open_files': [],
    'errors': [],
    'warnings': [],
    'ai_suggestions': {}
}

def update_plan(plan_data):
    """Update project plan"""
    PROJECT_STATE['plan'] = plan_data

def get_plan():
    """Get project plan"""
    return PROJECT_STATE.get('plan', {})

def add_error(error_msg, file_path=None):
    import datetime
    """Add error to state"""
    error = {
        'message': error_msg,
        'file': file_path,
        'timestamp': datetime.datetime.now()
    }
    PROJECT_STATE['errors'].append(error)

def clear_errors():
    """Clear all errors"""
    PROJECT_STATE['errors'] = []

def add_suggestion(file_path, suggestion):
    """Add AI suggestion"""
    if file_path not in PROJECT_STATE['ai_suggestions']:
        PROJECT_STATE['ai_suggestions'][file_path] = []
    PROJECT_STATE['ai_suggestions'][file_path].append(suggestion)

def clear_suggestions():
    """Clear all suggestions"""
    PROJECT_STATE['ai_suggestions'] = {}