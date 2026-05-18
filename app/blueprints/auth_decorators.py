"""Shared auth decorators for consistent access control"""

from functools import wraps
from flask_login import current_user
from flask import jsonify, redirect, url_for, flash


def contributor_or_admin_required(f):
    """Decorator: require contributor or admin role"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "please login to continue"}), 401
        if current_user.role not in ["contributor", "admin"]:
            return jsonify({"success": False, "error": "Access denied, contributor privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def contributor_or_admin_required_html(f):
    """Decorator: require permissions for HTML endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import render_template_string
        if not current_user.is_authenticated:
            flash("Please Login to continue", "error")
            return redirect(url_for("auth.login"))
        if current_user.role not in ["contributor", "admin"]:
            return render_template_string("<html><body><h1>Access denied</h1><p>Contributor privileges required.</p></body></html>"), 403
        return f(*args, **kwargs)

    return decorated_function