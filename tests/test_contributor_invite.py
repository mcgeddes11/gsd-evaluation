import pytest

from app.utils.tokens import generate_contributor_invite_token
from app.models.user import User

@pytest.mark.auth
class TestContributorInvite:

    def test_invite_page_requires_admin(self, client, contributor_user):
        response = client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        }, follow_redirects=False)

        response = client.get('/admin/invite', follow_redirects=False)
        assert response.status_code == 302 # redirect to login
        assert b'/auth/login' in response.data or response.location == '/auth/login'

    def test_invite_page_loads_for_admin(self, client, admin_user):
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=False)
        response = client.get('/admin/invite')
        assert response.status_code == 200
        assert b'Invite Contributor' in response.data

    def test_send_invite_email(self, client, admin_user, app):
        from app import mail
        # login as admin
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=True)

        with mail.record_messages() as outbox:
            response = client.post('/admin/invite', data={
                'email': "newuser@test.local",
                'role': 'contributor'
            }, follow_redirects=True)

            assert b'Invitation sent' in response.data
            assert len(outbox) == 1
            assert 'newuser@test.local' in outbox[0].recipients

    def test_invite_prevents_duplicate_email(self, client, admin_user):
        # login as admin
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        }, follow_redirects=True)

        response = client.post('/admin/invite', data={
            'email': admin_user.email,
            'role': 'contributor'
        }, follow_redirects=True)

        assert b'exists already' in response.data

@pytest.mark.auth
class TestContributorRegistration:

    def test_register_page_loads_with_valid_token(self, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        client = app.test_client()
        response = client.get(f'/auth/register/{token}')
        assert response.status_code == 200
        assert b'Complete Registration' in response.data

    def test_register_rejects_invalid_token(self, client):
        response = client.get('/auth/register/invalid-token', follow_redirects=True)
        assert b'Link expired or invalid' in response.data

    def test_register_creates_user(self, client, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        response = client.post(f'/auth/register/{token}', data={
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        assert b'Registration complete' in response.data

        with app.app_context():
            user = User.query.filter_by(email='newuser@test.local').first()
            assert user is not None
            assert user.role == 'contributor'
            assert user.is_active
            assert user.check_password('password123')

    def test_register_prevents_duplicate_registration(self, client, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        client.post(f'/auth/register/{token}', data={
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        # Second attempt should fail
        response = client.post(f'/auth/register/{token}', data={
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        assert b'already exists' in response.data

    def test_register_enforces_passwords_match(self, client, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        response = client.post(f'/auth/register/{token}', data={
            'password': 'password123',
            'password_confirm': 'other-password'
        }, follow_redirects=True)

        assert b'Passwords must match' in response.data

    def register_enforces_minimum_password_length(self, client, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        response = client.post(f'/auth/register/{token}', data={
            'password': 'abc',
            'password_confirm': 'abc'
        }, follow_redirects=True)

        assert b'at least 8 characters' in response.data

    def test_new_user_can_login(self, client, app):
        with app.app_context():
            token = generate_contributor_invite_token('newuser@test.local')

        client.post(f'/auth/register/{token}', data={
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        # Login
        response = client.post('/auth/login', data={
            'email': 'newuser@test.local',
            'password': 'password123'
        }, follow_redirects=False)

        assert response.status_code == 302 # redirect on success
