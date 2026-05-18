import os

class Config:
    """Base config share across environments"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://blog.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-in-production")

    # MEdia upload config
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # 10MB limit

    # Cloud carousel
    # Use any absolute path (ie. from uploads) or public URL
    # Empty disables the feature
    CAROUSEL_IMAGES = []

    # Main config
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = os.getenv("MAIL_PORT", 587)
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@blog.local")
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", False)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    MAIL_SUPPRESSED_SEND = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://:memory:"
    MAIL_SUPPRESS_SEND = True
    WTF_CSRF_ENABLED = False # Disable csrf in tests

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
