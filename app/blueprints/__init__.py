from flask import Blueprint, render_template, request, abort, send_from_directory, current_app
from flask_login import current_user
from app import db
from app.models.post import Post
import os
from app.blueprints.auth import auth_bp

main_bp = Blueprint("main", __name__)

@main_bp.route('/avatar/<path:filename>')
def serve_avatar(filename):
    """Serves user avatar to render on post cards"""
    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    # Prevent traversal
    safe_path = os.path.abspath(os.path.join(upload_folder, filename))
    if not safe_path.startswith(upload_folder):
        abort(403)
    return send_from_directory(upload_folder, filename)

@main_bp.route("/")
def index():
    """Public blog index"""
    # Get the posts
    page = request.args.get("page", 1, type=int)
    query = Post.query.filter_by(status="published").order_by(Post.published_at.desc())
    # Filter if search query is present
    search_query = request.args.get("q",'', type=str).strip()
    if search_query:
        # Escape SQL wildcards
        escaped = search_query.replace("\\","\\\\").replace("%", "\\%").replace('_','\\_')
        # case insensitive search
        query = query.filter(
            (Post.title.ilike(f'%{escaped}%', escape='\\')) |
            (Post.body.ilike(f'%{escaped}%', escape='\\'))
        )
    # Paginate
    posts_page = query.paginate(page=page, per_page=10)
    carousel_images = current_app.config.get("CAROUSEL_IMAGES", [])
    return render_template("public/index.html", posts_page=posts_page, search_query=search_query, carousel_images=carousel_images)

@main_bp.route("/posts/<slug>")
def post_detail(slug):
    """Public post detail page, read individual post"""
    post = Post.query.filter_by(slug=slug, status="published").first_or_404()

    # increment view count only for unauth'd users
    if not current_user.is_authenticated:
        post.view_count += 1
        db.session.commit()

    return render_template('public/post.html', post=post)
