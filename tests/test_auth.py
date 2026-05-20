import pytest
from flask import session
from app.models.user import User

@pytest.mark.auth
class TestLogin:


    def test_login_page_loads(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'<input' in response.data
        assert b'type="email"' in response.data
        assert b'type="password"' in response.data
        assert b'Sign In' in response.data

    def test_login_with_valid_credentials(self, client, admin_user):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_creates_session_cookie(self, client, admin_user, app):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert response.headers.get("Set-Cookie").startswith("session=")

    def test_login_with_invalid_password(self, client, admin_user):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'fubar'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_with_nonexistent_email(self, client):
        response = client.post('/auth/login', data={
            'email': 'nobody@test.local',
            'password': 'some-password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_with_missing_email(self, client):
        response = client.post('/auth/login', data={
            'email': '',
            'password': 'some-password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Email and password are required' in response.data

    def test_login_with_missing_password(self, client):
        response = client.post('/auth/login', data={
            'email': 'admin@test.local',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Email and password are required' in response.data

    def test_login_with_inactive_user(self, client, app):
        with app.app_context():
            from app import db
            user = User(email='inactive@test.local', role='admin', is_active=False)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        response = client.post('/auth/login', data={
            'email': 'inactive@test.local',
            'password': 'password'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'deactivated' in response.data

    def test_login_remember_me(self, client, admin_user):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password',
            'remember_me': 'on'
        }, follow_redirects=False)

        assert response.status_code == 302

@pytest.mark.auth
class TestLogout:

    def test_logout_requires_login(self, client):
        response = client.post('/auth/logout', follow_redirects=False)
        assert response.status_code == 302

    def test_logout_invalidates_session(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        client.post('/auth/logout', follow_redirects=False)
        response = client.get('/admin/posts', follow_redirects=False)
        # TODO: assert session cookie is deleted
        assert response.status_code == 302

    def test_logout_redirects_to_public_blog(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        response = client.post('/auth/logout', follow_redirects=False)
        assert response.location == '/'



@pytest.mark.auth
class TestSessionPersistence:

    def test_session_persists_across_page_refresh(self, client, admin_user):
        response1 = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=True)

        assert response1.status_code == 200
        # TODO: validate session tokens match before and after
        # Make another request to simulate refresh. for now just check subsequent requests don't error
        response2 = client.get('/')
        assert response2.status_code in [200,302]



@pytest.mark.auth
class TestAccessControl:

    def test_admin_dashboard_requires_auth(self, client):
        response = client.get('/admin/dashboard', follow_redirects=False)
        # should redirect to login page
        assert response.status_code == 302


    def test_admin_dashboard_accessible_when_logged_in(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        response = client.get('/admin/dashboard')
        assert response.status_code == 200

@pytest.mark.auth
class TestAlreadyAuthenticated:

    def test_login_redirects_if_authenticated(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })
        response = client.get('/auth/login', follow_redirects=False)
        assert response.status_code == 302





