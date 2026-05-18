import click
from flask.cli import with_appcontext
from app import db, bcrypt
from app.models.user import User

@click.command('create-admin')
@click.option('--email', prompt='Admin email', help='Email address for admin account')
@click.option('--password', prompt=True, confirmation_prompt=True, help="Admin password")
@with_appcontext
def create_admin_command(email, password):
    """Create first admin account (error if already exists)"""
    # Check admin exists
    admin_exists = User.query.filter_by(role="admin").first()
    if admin_exists:
        click.echo(f"Error: Admin account already exists ({admin_exists.email})", err=True)
        return

    # Check if user with this email already exists
    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        click.echo(f"Error: User account already exists ({user_exists.email})", err=True)

    # Create admin user
    admin = User(email=email, role='admin', is_active=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    click.echo(f"Admin account created: {email}")