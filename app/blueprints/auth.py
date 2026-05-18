from flask import Blueprint, render_template, request,  redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import db, mail, login_manager
from app.models.user import User
from app.utils.tokens import generate_password_reset_token, verify_password_reset_token, verify_contributor_invite_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def url_has_allowed_host_and_scheme(url, allowed_hosts=None):
    """Check if a redirect is safe"""
    from urllib.parse import urlparse
    if allowed_hosts is None:
        allowed_hosts = set()
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc in allowed_hosts



@auth_bp.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login with email and password"""

    if current_user.is_authenticated:
        if current_user.user_role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('posts.list_posts'))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        remember_me = request.form.get("remember_me")

        # Validate input
        if not email or not password:
            flash("Email and password required", "error")
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        # Verify credentials
        if not user or not user.check_password(password):
            flash("Invalid username or password, please try again", "error")
            return redirect(url_for('auth.login'))

        # check account active
        if not user.is_active:
            flash("This account has been deactivated, contact your administrator", "error")
            return redirect(url_for('auth.login'))

        # Create session
        login_user(user, remember=bool(remember_me))

        # Redirect to next page or role-appropriate home page
        next_page = request.args.get("next")
        if next_page and url_has_allowed_host_and_scheme(next_page):
            return redirect(next_page)
        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("posts.list_posts"))
    return render_template("auth/login.html")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Signed out successfully", "success")
    return redirect(url_for("main.index"))

@auth_bp.route("/logout-confirm", methods=["GET"])
@login_required
def logout_confirm():
    return render_template("auth/logout_confirmation.html")

# TODO: forgot password, reset password, register





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
















