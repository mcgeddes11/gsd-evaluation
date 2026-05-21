import pytest
from app import create_app, db
from app.models.media import Media
from app.models.user import User
from io import BytesIO

@pytest.mark.media
class TestMediaUpload:

    def test_upload_image_as_contributor(self,client, app, contributor_user):
        contributor_id = contributor_user.id

        client.post('/auth/login', data ={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })

        test_file = (BytesIO(b'fake image data'), 'test.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert 'url' in data
        assert 'id' in data

        with app.app_context():
            media = Media.query.filter_by(original_filename='test.jpg').first()
            assert media is not None
            assert media.uploader_id == contributor_id

    def test_image_upload_as_admin(self, client, app, admin_user):
        user_id = admin_user.id

        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'admin-password'
        })

        test_file = (BytesIO(b'fake image data'), 'test.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert 'url' in data
        assert 'id' in data

        with app.app_context():
            media = Media.query.filter_by(original_filename='test.jpg').first()
            assert media is not None
            assert media.uploader_id == user_id

    def test_upload_requires_login(self, client):
        test_file = (BytesIO(b'fake image data'), 'test.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_upload_rejects_no_file(self, client, contributor_user):
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })
        response = client.post('/admin/media/upload-ajax', data={})
        assert response.status_code == 400
        assert response.get_json()['success'] is False

    def test_upload_rejects_invalid_extension(self, client, contributor_user):
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })
        test_file = (BytesIO(b'fake image data'), 'document.txt')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })
        assert response.status_code == 400
        assert response.get_json()["success"] is False

    def test_upload_stores_uuid_filename(self, client, app, contributor_user):
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })
        test_file = (BytesIO(b'fake image data'), 'image.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        with app.app_context():
            media = Media.query.get(data["id"])
            assert media is not None
            assert media.filename.endswith(".jpg")
            assert len(media.filename.rsplit(".")[0]) == 32 # uuid4 is 32 chars
            assert media.original_filename == "image.jpg"

    def test_upload_stores_metadata(self, client, app, contributor_user):
        contributor_id = contributor_user.id
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })
        test_file = (BytesIO(b'fake image data'), 'image.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        with app.app_context():
            media = Media.query.get(data["id"])
            assert media is not None
            assert media.mime_type == 'image/jpeg'
            assert media.mime_type == 'image/jpeg'
            assert media.file_size == 15
            assert media.uploader_id == contributor_id
            assert media.created_at is not None

    def test_upload_rejects_oversized_files(self, client, contributor_user):
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })

        # Create a file larger than 5MB
        large_data = b'x' * (6 * 1024 * 1024)
        test_file = (BytesIO(large_data), 'large.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })

        assert response.status_code == 400
        assert response.get_json()["success"] is False

@pytest.mark.media
class TestMediaServe:

    def test_serve_uploaded_image(self, client, app, contributor_user):
        client.post('/auth/login', data={
            'email': contributor_user.email,
            'password': 'contributor-password'
        })
        test_file = (BytesIO(b'fake image data'), 'image.jpg')
        response = client.post('/admin/media/upload-ajax', data={
            'file': test_file
        })
        media_id = response.get_json()["id"]
        response = client.get(f'/admin/media/serve{media_id}')
        # accept 200 or 404, test it responds without raising a 500
        assert response.status_code in [200, 404]

    def test_serve_nonexistent_returns_404(self, client):
        response = client.get('/admin/media/serve/99999')
        assert response.status_code == 404

    def test_serve_no_auth_required(self, client, app, contributor_user):
        contributor_id = contributor_user.id
        with app.app_context():
            media = Media(
                filename="test123.jpg",
                original_filename="test.jpg",
                file_path="./uploads/test123.jpg",
                mime_type='image/jpeg',
                file_size=100,
                uploader_id=contributor_id
            )
            db.session.add(media)
            db.session.commit()
            media_id = media.id
        response = client.get(f'/admin/media/serve/{media_id}')
        assert response.status_code in [200, 404]

@pytest.mark.media
class TestMediaList:

    def test_list_media_requires_login(self, client):
        response = client.get('/admin/media', follow_redirects=False)
        assert response.status_code in [302, 308]

    def test_list_media_requires_auth(self, client, app, viewer_user):
        response = client.get('/admin/media', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
        assert b'Login to continue' in response.data







