import os
from fileinput import filename

from flask import url_for

class Config:
    """Base config share across environments"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////app/instance/blog.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-in-production")

    # MEdia upload config
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # Flask request ceiling
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024 # 5 MB per file limit enforced in media blueprint
    USER_STORAGE_QUOTA = 500 * 1024 * 1024 # 500MB storage max per user

    # Cloud carousel
    # Use any absolute path (ie. from uploads) or public URL
    # Empty disables the feature
    CAROUSEL_IMAGES = ["https://blog.mcgeddes.com/admin/media/serve/147",
                       "https://blog.mcgeddes.com/admin/media/serve/148",
                       "https://blog.mcgeddes.com/admin/media/serve/149",
                       "https://blog.mcgeddes.com/admin/media/serve/150",
                       "https://blog.mcgeddes.com/admin/media/serve/151",]

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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'blog.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MAIL_SUPPRESS_SEND = True
    WTF_CSRF_ENABLED = False # Disable csrf in tests
    UPLOAD_FOLDER = None

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = 'https'
