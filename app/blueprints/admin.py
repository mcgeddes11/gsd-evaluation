from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db, mail
from app.models.user import User
from app.utils.tokens import generate_contributor_invite_token
from flask_mail import Message
from functools import wraps
from werkzeug.utils import secure_filename
import os
import uuid

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator: require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Access denied, admind privileges required", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    return render_template('admin/dashboard.html', total_users=total_users, active_users=active_users)

@admin_bp.route('/accounts', methods=["GET"])
@login_required
@admin_required
def accounts_list():
    """List all user accounts"""
    page = request.args.get("page", 1, type=int)
    accounts=User.query.paginate(page=page, per_page=10)
    return render_template('admin/accounts.html', accounts=accounts)

@admin_bp.route('/accounts/<int:user_id>/deactivate', methods=["POST"])
@login_required
@admin_required
def deactivate_account(user_id):
    """Deactivate a user account (admin only)"""
    if user_id == current_user.id:
        flash("Cannot deactivate your own account","error")
        return redirect(url_for("admin.accounts_list"))
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Cannot deactivate admin accounts", "error")
        return redirect(url_for("admin.accounts_list"))

    user.is_active = False
    db.session.commit()
    flash(f'Account {user.email} has been deactivated', "success")
    return redirect(url_for("admin.accounts_list"))

@admin_bp.route('/accounts/<int:user_id>/reactivate', methods=["POST"])
@login_required
@admin_required
def reactivate_account(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'Account {user.email} reactivated', "success")
    return redirect(url_for("admin.accounts_list"))

@admin_bp.route('/accounts/<int:user_id>/delete', methods=["POST"])
@login_required
@admin_required
def delete_account(user_id):
    """Delete a user account permanently"""
    # Prevent from deleting themselves
    if user_id == current_user.id:
        flash("Cannot delete your own account", "error")
        return redirect(url_for("admin.accounts_list"))
    user = User.query.get_or_404(user_id)
    email = user.email
    db.session.delete(user)
    db.session.commit()
    flash(f'Account {email} has been deleted', "success")
    return redirect(url_for("admin.accounts_list"))

@admin_bp.route('/invite', methods=["GET", "POST"])
@login_required
@admin_required
def invite_contributor():
    """Send invitation email to a contributor"""
    if request.method == "POST":
        email = request.form.get("email", '').strip()
        role = request.form.get("role", 'contributor').strip()

        if not email:
            flash("Email is required", "error")
            return redirect(url_for('admin.invite_contributor'))

        if role not in ["admin", "contributor"]:
            flash("Invalid role", "error")
            return redirect(url_for('admin.invite_contributor'))

        # Check user exists already
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(f'User {email} exists already", "error')
            return redirect(url_for('admin.invite_contributor'))

        # generate invite token
        token = generate_contributor_invite_token(email)
        register_url = url_for("auth.register", token=token, _external=True)

        from flask import current_app
        if current_app.config.get("MAIL_SUPPRESS_SEND"):
            print(f'[DEV] Contributor invite link for {email}: {register_url}', flush=True)

        # Send invite email
        msg = Message(
            subject="You've been invited to join the blog",
            recipients=[email],
            html=render_template("email/contributor_invite.html", register_url=register_url, email=email, role=role),
            body=render_template("email/contributor_invite.txt", register_url=register_url, email=email, role=role),
        )
        mail.send(msg)

        flash(f"Invitation sent to {email}. They'll receive an email with a registration link", "success")
        return redirect(url_for('admin.invite_contributor'))
    return render_template('admin/invite_contributor.html')

_AVATAR_ALLOWED = {"jpg", "jpeg", "png", "gif", "webp"}

@admin_bp.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    """Profile page, update name and avatar"""
    if request.method == "POST":
        first_name = request.form.get("first_name", '').strip() or None
        last_name = request.form.get("last_name", '').strip() or None
        current_user.first_name = first_name
        current_user.last_name = last_name

        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            ext = avatar.filename.rsplit(".", 1)[-1].lower() if "." in avatar.filename else ""
            if ext not in _AVATAR_ALLOWED:
                flash(f"Avatar must be of format: {",".join(_AVATAR_ALLOWED)}", "error")
                return redirect(url_for("admin.profile"))
            upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
            os.makedirs(upload_folder, exist_ok=True)

            # Remove old one if present
            if current_user.avatar_filename:
                old_path = os.path.join(upload_folder, current_user.avatar_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            filename = f"avatar_{uuid.uuid4().hex}.{ext}"
            avatar.save(os.path.join(upload_folder, filename))
            current_user.avatar_filename = filename

        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html")




