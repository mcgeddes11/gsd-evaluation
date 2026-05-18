from flask import Blueprint, render_template, jsonify, request, url_for, current_app, redirect, flash
from flask_login import login_required, current_user
from app import db, csrf
from app.blueprints.auth import login
from app.models.media import Media
from app.blueprints.admin import admin_required, admin_bp
from app.blueprints.auth_decorators import contributor_or_admin_required, contributor_or_admin_required_html
from werkzeug.utils import secure_filename
from sqlalchemy import func
import os
import uuid

media_bp = Blueprint("media", __name__, url_prefix="/admin/media")

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_image_file(filename, content_type=None):
    """Check if file has allowed extension and mime type"""
    if "." not in filename:
        return False

    ext = filename.split(".")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    # Verify MIME type
    if content_type:
        allowed_mimes = {
            "jpg": ["image/jpeg"],
            "jpeg": ["image/jpeg"],
            "png": ["image/png"],
            "gif": ["image/gif"],
            "webp": ["image/webp"]
        }
        if content_type not in allowed_mimes.get(ext,[]):
            return False

    return True


@media_bp.route("/upload-ajax", methods=["POST"])
@login_required
@contributor_or_admin_required
def upload_ajax():
    """Handle ajax image upload from editor"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "no file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_image_file(file.filename, file.content_type):
        return jsonify({"success": False, "error": "Invalid file type. Allowed file types: JPG, PNG, GIF, WebP"}), 400

    try:
        # Check file size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()

        max_upload_size = current_app.config["MAX_UPLOAD_SIZE"]
        if file_length > max_upload_size:
            file.seek(0)
            return jsonify({"success": False, "error": f'File too large. Max {max_upload_size // (1024 * 1024)} MB'}), 400
        file.seek(0)

        # Check quota for this user
        user_total = db.session.query(func.sum(Media.file_size)).filter_by(uploader_id=current_user.id).scalar() or 0
        # TODO: make this a per-user configurable on the User model rather than a blanket config setting
        user_quota = current_app.config["USER_STORAGE_QUOTA"]
        if user_total + file_length > user_quota:
            return jsonify({"success": False, "error": f'Storage quota exceeded. Max {user_quota // (1024 *1024)} MB per user'}), 400

        # Generate UUID filename
        ext = file.filename.rsplit(".",1)[1].lower()
        uuid_filename = f"{uuid.uuid4().hex}.{ext}"

        # Ensure uploads folder exists
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        # Save
        file_path = os.path.join(upload_folder, uuid_filename)
        file.save(file_path)

        media = Media(
            filename=uuid_filename,
            original_filename=secure_filename(file.filename),
            file_path=file_path,
            mime_type=file.content_type or "image/jpeg",
            file_size=file_length,
            uploader_id=current_user.id
        )
        db.session.add(media)
        db.session.commit()

        # Log successful upload
        current_app.logger.info(f"Media uploaded: {uuid_filename} by user {current_user.id}")

        # Return json with URL for Quill editor to insert
        url = url_for("media.serve", media_id=media.id, _external=False)
        return jsonify(
            {
                "success": True,
                "url": url,
                "id": media.id
            }
        ), 200
    except IOError as e:
        db.session.rollback()
        current_app.logger.error(f'Disk error during upload {e}')
        return jsonify({"success": False, "error": "Failed to save file to disk"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Unexpected error during upload: {e}')
        return jsonify({"success": False, "error": "Unexpected error occurred"})

@media_bp.route("/serve/<int:media_id>", methods=["GET"])
def serve(media_id):
    """Serve media file - public but blocks iteration"""
    from flask import send_from_directory, abort

    media = Media.query.get_or_404(media_id)

    # serve file - auth not required
    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    file_path = os.path.join(upload_folder)
    requested_path = os.path.abspath(file_path)

    if not requested_path.startswith(upload_folder):
        abort(403)

    if not os.path.exists(file_path):
        current_app.logger.warning(f'Media file not found: {file_path}')
        abort(404)

    try:
        return send_from_directory(
            upload_folder,
            media.filename,
            mimetype=media.mime_type
        )
    except Exception as e:
        current_app.logger.error(f'Error serving media {media_id}: {str(e)}')
        abort(404)


@media_bp.route('/', methods=["GET"])
@contributor_or_admin_required_html
@login_required
def list_media():
    """List all media with pagination"""
    page = request.args.get("page", 1, type=int)
    media = Media.query.paginate(page=page, per_page=10)
    return render_template('media/list.html', media=media)

@media_bp.route('/upload-form', methods=["GET"])
@login_required
@contributor_or_admin_required_html
def upload_form():
    """Show media upload form"""
    return render_template("media/upload.html")


@media_bp.route("/<int:media_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(media_id):
    """Delete media (admin only)"""
    media = Media.query.get_or_404(media_id)

    original_filename = media.original_filename
    file_path = media.file_path

    try:
        # Delete from db first
        db.session.delete(media)
        db.session.commit()

        # Log deletion
        current_app.logger.info(f"Media deleted: {original_filename} (ID: {media_id} by user {current_user.id}")

        # Clean up filesystem
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                current_app.logger.error(f'Failed to delete file {file_path}: {e}')
                flash(f'Media deleted from database but file cleanup failed', "warning")
                return redirect(url_for("media.list_media"))
        flash(f'Media "{original_filename}" has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to delete media: {media_id}: {e}')
        flash(f"Failed to delete media", "error")
    return redirect(url_for("media.list_media"))
