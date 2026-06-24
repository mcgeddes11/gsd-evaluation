from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.post import Post
from app.blueprints.admin import admin_required
from app.blueprints.auth_decorators import contributor_or_admin_required_html
from app.utils.slugify import generate_slug, validate_slug
from app.utils.sanitize import sanitize_html
from functools import wraps
from datetime import datetime

posts_bp = Blueprint('posts', __name__, url_prefix='/admin/posts')

# TODO: implement domain whitelist for iframe insertion here if required

def _apply_post_form(post, error_redirect):
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    slug = request.form.get('slug', '').strip()
    status = request.form.get('status', 'draft').strip()

    # validation
    if not title:
        flash("Post title is required", 'error')
        return redirect(error_redirect)

    if not body:
        flash("Post body is required", 'error')
        return redirect(error_redirect)

    if not slug:
        slug = generate_slug(title)
    elif slug != post.slug:
        if not validate_slug(slug):
            flash("Invalid slug format. Lowercase letters, numbers, hyphens and underscores only")
            return redirect(error_redirect)
        q = Post.query.filter_by(slug=slug)
        if post.id is not None:
            q = q.filter(Post.id != post.id)
        if q.first():
            flash(f'A post with slug "{slug}" already exists. Please choose a different slug/title.')
            return redirect(error_redirect)
    post.title = title
    post.body = sanitize_html(body)
    post.slug = slug
    post.status = status
    if status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
    elif status == "draft":
        post.published_at = None
    return None

def owner_or_admin_required(model_class):
    """Decorator to check post ownership or admin role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            post_id = kwargs.get('post_id')
            if not post_id:
                abort(400)
            post = model_class.query.get_or_404(post_id)
            # Check user
            if current_user.id != post.author_id and current_user.role != 'admin':
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@posts_bp.route('', methods=["GET"])
@login_required
@contributor_or_admin_required_html
def list_posts():
    """list posts with pagination"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('posts/list.html', posts=posts)

@posts_bp.route("/create", methods=["GET"])
@login_required
@contributor_or_admin_required_html
def create_form():
    """Show create post form"""
    return render_template("posts/editor.html", post=None)

@posts_bp.route("/create", methods=["POST"])
@login_required
@contributor_or_admin_required_html
def create():
    """Create a new post"""
    post = Post(author_id=current_user.id)
    err = _apply_post_form(post, url_for('posts.create_form'))
    if err:
        return err

    db.session.add(post)
    db.session.commit()

    if request.form.get('preview') == '1':
        return redirect(url_for('posts.edit_form', post_id=post.id, preview='1'))

    flash(f'Post "{post.title}" created successfully', "success")
    return redirect(url_for('posts.list_posts'))


@posts_bp.route('/<int:post_id>/edit', methods=["GET"])
@login_required
@contributor_or_admin_required_html
@owner_or_admin_required(Post)
def edit_form(post_id):
    post = Post.query.get_or_404(post_id)
    if post.status == "published":
        flash("Unpublish this post before editing", "error")
        return redirect(url_for('posts.list_posts'))
    preview = request.args.get('preview') == '1'
    return render_template('posts/editor.html', post=post, open_preview=preview)


@posts_bp.route('/<int:post_id>/edit', methods=["POST"])
@login_required
@contributor_or_admin_required_html
@owner_or_admin_required(Post)
def edit(post_id):
    """Update existing post"""
    post = Post.query.get_or_404(post_id)
    if post.status == "published":
        flash("Unpublish this post before editing", "error")
        return redirect(url_for('posts.list_posts'))

    err = _apply_post_form(post, url_for('posts.edit_form', post_id=post_id))
    if err:
        return err

    db.session.commit()

    if request.form.get('preview') == '1':
        return redirect(url_for('posts.edit_form', post_id=post.id, preview='1'))

    flash(f'Post "{post.title}" updated successfully.', "success")
    return redirect(url_for('posts.list_posts'))


@posts_bp.route('/<int:post_id>/preview', methods=["GET"])
@login_required
@contributor_or_admin_required_html
@owner_or_admin_required(Post)
def preview(post_id):
    """Render a draft post using the public template"""
    post = Post.query.get_or_404(post_id)
    return render_template('public/post.html', post=post)

@posts_bp.route('/<int:post_id>/delete', methods=["POST"])
@login_required
@admin_required
def delete(post_id):
    """delete a post, requires admin"""
    post = Post.query.get_or_404(post_id)
    title = post.title

    db.session.delete(post)
    db.session.commit()

    flash(f'Post "{title}" deleted', "success")
    return redirect(url_for('posts.list_posts'))

@posts_bp.route('/<int:post_id>/publish', methods=["POST"])
@login_required
@contributor_or_admin_required_html
def publish(post_id):
    """Publish a post"""
    post = Post.query.get_or_404(post_id)

    # Check ownership
    if current_user.id != post.author_id and current_user.role != "admin":
        abort(403)

    if post.status == "published":
        flash("Post is already published", "info")
        return redirect(url_for("posts.list_posts"))

    post.status = "published"
    if not post.published_at:
        post.published_at = datetime.utcnow()
    db.session.commit()

    flash('Post published successfully', "success")
    return redirect(url_for('posts.list_posts'))


@posts_bp.route('/<int:post_id>/unpublish', methods=["POST"])
@login_required
@contributor_or_admin_required_html
def unpublish(post_id):
    """Unpublish a post"""
    post = Post.query.get_or_404(post_id)

    # Check ownership
    if current_user.id != post.author_id and current_user.role != "admin":
        abort(403)

    if post.status == "draft":
        flash("Post is already draft", "info")
        return redirect(url_for("posts.list_posts"))

    post.status = "draft"
    post.published_at = None
    db.session.commit()

    flash('Post unpublished successfully', "success")
    return redirect(url_for('posts.list_posts'))


@posts_bp.route('/<int:post_id>/set-published-date', methods=["POST"])
@login_required
@contributor_or_admin_required_html
def set_published_date(post_id):
    """Manually set the published date on a published post"""
    post = Post.query.get_or_404(post_id)

    if current_user.id != post.author_id and current_user.role != "admin":
        abort(403)

    if post.status != "published":
        flash("Can only set published date on a published post", "error")
        return redirect(url_for('posts.list_posts'))

    raw = request.form.get('published_at', '').strip()
    try:
        post.published_at = datetime.strptime(raw, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format", "error")
        return redirect(url_for('posts.list_posts'))

    db.session.commit()
    flash(f'Published date updated to {post.published_at.strftime("%B %d, %Y")}', "success")
    return redirect(url_for('posts.list_posts'))


















