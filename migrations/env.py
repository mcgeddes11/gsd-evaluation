import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure project root is on system path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0,_project_root)

from app import db, create_app

# Alembic config object
config = context.config

# Interpret config for python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set slqalchemy url from app config, resolving sqlite paths to absolute
app = create_app(os.getenv("FLASK_ENV", "development").capitalize() + "Config")
db_url = app.config["SQLALCHEMY_DATABASE_URI"]
if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
    # Relative path - Flask resolves sqlite:///foo.db against the instance folder,
    # not the project root. Resolve it the same way so Alembic finds the right DB
    rel = db_url[len("sqlite:///"):]
    db_url = "sqlite:///" + os.path.join(app.instance_path, rel)
target_metadata = db.metadata

def run_migrations_offline() -> None:
    """Run migration in offline mode (print SQL to stdout)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_options={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations online mode (connect to an actual db)"""
    from sqlalchemy import create_engine
    connectable = create_engine(db_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
