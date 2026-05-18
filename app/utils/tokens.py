from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# TODO: Update salts to be env vars
# TODO: Consolidate logic

def get_serializer():
    """Get serializer using secret key"""
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_password_reset_token(email):
    """Generate single use password reset token (24 hour expiry)"""
    serializer = get_serializer()
    return serializer.dumps(email, salt="password-reset-salt")

def verify_password_reset_token(token, max_age=86400):
    """Verify password reset token and return email if any
    Returns email if token is valid and not expired
    Returns None if token is invalid, expired or already used
    Token deleted from DB after first use
    """
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=max_age)
        return email
    except Exception as e:
        # token invalid, expired or tampered with
        return None

def generate_contributor_invite_token(email):
    serializer = get_serializer()
    return serializer.dumps(email, salt="contributor-invite-salt")

def verify_contributor_invite_token(token, max_age=86400):
    """Verify password reset token and return email if any
    Returns email if token is valid and not expired
    Returns None if token is invalid, expired or already used
    Token deleted from DB after first use
    """
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="contributor-invite-salt", max_age=max_age)
        return email
    except Exception as e:
        # token invalid, expired or tampered with
        return None

