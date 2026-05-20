import pytest

from app.blueprints.admin import reactivate_account
from app.models.user import User

@pytest.mark.admin
class TestAdminDashboard:
    """Test admin access and auth"""

    def test_dashboard_requires_login(self, client):
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code in [302, 401]

    def test_dashboard_requires_admin_role(self, client, contributor_user):
        response = client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        }, follow_redirects=False)
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code == 302 # redirect to login
        assert b'/auth/login' in response.data or response.location == '/auth/login'

    def test_dashboard_loads_for_admin(self, client, admin_user):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=False)
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data

@pytest.mark.admin
class TestAccountManagement:
    """Test CRUD ops for accounts"""

    def test_account_list_requires_admin(self, client, contributor_user):
        response = client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        }, follow_redirects=False)
        response = client.get('/admin/accounts', follow_redirects=False)
        assert response.status_code == 302 # redirect to login
        assert b'/auth/login' in response.data or response.location == '/auth/login'

    def test_accounts_list_shows_users(self, client, admin_user, app):
        # Create additional users
        with app.app_context():
            from app import db
            user1 = User(email='user1@test.local', role='contributor', is_active=True)
            user1.set_password("password")
            user2 = User(email='user2@test.local', role='contributor', is_active=False)
            user2.set_password("password")
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

        client.post('/auth/login', data={
            'email': 'admin@test.local',
            'password': 'admin-password'
        })
        response = client.get('/admin/accounts')
        assert response.status_code == 200
        assert b'user1@test.local' in response.data
        assert b'user2@test.local' in response.data
        assert b'Active' in response.data
        assert b'Inactive' in response.data

    def test_deactivate_account(self, client, admin_user, app):
        # Create contributor
        with app.app_context():
            from app import db
            user = User(email='user@test.local', role='contributor', is_active=True)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        response = client.post(f'/admin/accounts/{user_id}/deactivate', follow_redirects=True)
        assert b'deactivated' in response.data

        with app.app_context():
            user = User.query.get(user_id)
            assert not user.is_active

    def test_reactivate_account(self, client, admin_user, app):
        with app.app_context():
            from app import db
            user = User(email='user@test.local', role='contributor', is_active=False)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            client.post('/auth/login', data={
                'email': admin_user.email,
                'password': 'admin-password'
            })
            response = client.post(f'/admin/accounts/{user_id}/reactivate', follow_redirects=True)
            assert b'reactivated' in response.data
            with app.app_context():
                user = User.query.get(user_id)
                assert user.is_active

    def test_delete_account(self, client, admin_user, app):
        # Create contributor
        with app.app_context():
            from app import db
            user = User(email='user@test.local', role='contributor', is_active=True)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        response = client.post(f'/admin/accounts/{user_id}/delete', follow_redirects=True)
        assert b'deleted' in response.data

        with app.app_context():
            user = User.query.get(user_id)
            assert user is None

    def test_deactivate_prevents_login(self, client, app):
        # Create contributor
        with app.app_context():
            from app import db
            user = User(email='user@test.local', role='contributor', is_active=False)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post('/auth/login', data={
            'email': 'user@test.local',
            'password': 'password'
        }, follow_redirects=True)

        assert b'deactivated' in response.data
