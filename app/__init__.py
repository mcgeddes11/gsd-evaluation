from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from alembic.config import Config as AlembicConfig

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class="DevelopmentConfig"):
    """Application factory - creates and configures Flask App"""
    from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
    config_map = {
        "DevelopmentConfig": DevelopmentConfig,
        "TestingConfig": TestingConfig,
        "ProductionConfig": ProductionConfig
    }

    config = config_map.get(config_class, DevelopmentConfig)
    app = Flask(__name__)
    app.config.from_object(config)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.blueprints import auth_bp, main_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.posts import posts_bp
    from app.blueprints.media import media_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(main_bp)

    # Register CLI commands
    from app.cli import create_admin_command
    app.cli.add_command(create_admin_command)

    # Create tables on first startup
    # TODO: run 'alembic upgrade head' from migrations directory first before running locally
    # with app.app_context():
    #     db.create_all()

    return app








