from functools import wraps
from flask import (current_app, session, redirect)
from flask_login import current_user


def auth_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        elif not session.get('authy'):
            return redirect('/auth')
        return func(*args, **kwargs)
    return decorated_view
