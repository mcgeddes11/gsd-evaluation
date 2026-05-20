import uuid
from app import db
from app.models.post import Post
from app.utils.slugify import generate_slug


def post_factory(app, admin_user=None, title=None, slug=None, status='draft'):
    """
    Factory function for creating test posts


    :param app: Flask app instance
    :param admin_user: User object to assign as author (required)
    :param title: Post title (default: "Test post {uuid{")
    :param slug: Post slug (Default: generated from title)
    :param status: Post status (Default 'draft')
    :return: Post object committed to db
    """
    if admin_user is None:
        raise ValueError("admin_user is required")

    # generate title if not provided
    if title is None:
        title = f"Test Post {uuid.uuid4().hex[:8]}"

    # generate slug from title
    if slug is None:
        slug = generate_slug(title)

    # Create post
    post = Post(
        title=title,
        slug=slug,
        body="This is test post content in Markdown",
        status=status,
        author_id=admin_user.id
    )
    db.session.add(post)
    db.session.commit()
    return post

