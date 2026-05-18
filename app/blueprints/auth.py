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

@auth_bp.route('/forgot_password', methods=["GET","POST"])
def forgot_password():
    """Handle forgot password flow"""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("posts.list_posts"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            flash("Email address required", "error")
            return redirect(url_for("auth.forgot_password"))

        user = User.query.filter_by(email=email).first()

        if user:
            # generate a token
            token = generate_password_reset_token(email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            # Log reset URL to console in dev mode
            from flask import current_app
            if current_app.config.get("MAIL_SUPPRESS_SEND"):
                print(f'[DEV] Password reset link for {email}: {reset_url}', flush=True)

            msg = Message(
                subject="Password reset request",
                recipients=[email],
                html=render_template("email/password_reset.html", reset_url=reset_url, user=user),
                body=render_template("email/password_reset.txt", reset_url=reset_url, user=user)
            )
            mail.send(msg)
        flash("Check your email for a password reset link. Link expires in 24 hours", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset"""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("posts.list_posts"))

    email = verify_password_reset_token(token)

    if not email:
        flash("Link expired or invalid. Please request a new password reset link", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not password or not password_confirm:
            flash("Both password fields are required", "error")
            return redirect(url_for("auth.reset_password", token=token))
        if password != password_confirm:
            flash("Passwords must match", "error")
            return redirect(url_for("auth.reset_password", token=token))
        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return redirect(url_for("auth.reset_password", token=token))

        # find user and update password
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found, contact your administrator", "error")
            return redirect(url_for("auth.login"))

        user.set_password(password)
        db.session.commit()

        # token is invalidated
        flash("Password was updated successfully. Please sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password", token=token)

@auth_bp.route("/register/<token>", methods=["GET","POST"])
def register(token):
    """Handle registration via invite link"""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("posts.list_posts"))

    email = verify_contributor_invite_token(token)

    if not email:
        flash("Link expired or invalid. Please contact your administrator for a new invite", "error")
        return redirect(url_for("auth.login"))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash(f"Account with {email} already exists. Please log in instead", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not password or not password_confirm:
            flash("Both password fields are required", "error")
            return redirect(url_for("auth.register", token=token))
        if password != password_confirm:
            flash("Passwords must match", "error")
            return redirect(url_for("auth.register", token=token))
        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return redirect(url_for("auth.register", token=token))

        # create new account
        new_user = User(email=email, role="contributor", is_active=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration complete! Please log in with your credentials", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", email=email, token=token)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
















