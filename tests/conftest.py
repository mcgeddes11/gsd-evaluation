import pytest
import tempfile
import shutil
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    """create app for testing"""
    tmp_upload_dir = tempfile.mkdtemp()
    app = create_app('TestingConfig')
    app.config["UPLOAD_FOLDER"] = tmp_upload_dir

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    shutil.rmtree(tmp_upload_dir, ignore_errors=True)

@pytest.fixture
def client(app):
    """test client for making requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing commands"""
    return app.test_cli_runner()

from collections import namedtuple

UserStub = namedtuple('UserStub', ['id', 'email', 'role'])

@pytest.fixture
def admin_user(app):
    """create an admin user for testing"""
    with app.app_context():
        admin = User(email='admin@test.local', role='admin', is_active=True)
        admin.set_password('admin-password')
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id
    # Return as namedtuple for use outside of context
    return UserStub(id=admin_id, email='admin@test.local', role='admin')

@pytest.fixture
def contributor_user(app):
    """create a contributor user for testing"""
    with app.app_context():
        contributor = User(email='contributor@test.local', role='contributor', is_active=True)
        contributor.set_password('contributor-password')
        db.session.add(contributor)
        db.session.commit()
        contributor_id = contributor.id
    # Return as namedtuple for use outside of context
    return UserStub(id=contributor_id, email='contributor@test.local', role='contributor')

@pytest.fixture
def viewer_user(app):
    """create a viewer user for testing"""
    with app.app_context():
        viewer = User(email='viewer@test.local', role='viewer', is_active=True)
        viewer.set_password('viewer-password')
        db.session.add(viewer)
        db.session.commit()
        viewer_id = viewer.id
    # Return as namedtuple for use outside of context
    return UserStub(id=viewer, email='viewer@test.local', role='viewer')
