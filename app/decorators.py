from flask import abort
from flask_login import current_user
from functools import wraps

def role_required(expected_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != expected_role:
                return abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
