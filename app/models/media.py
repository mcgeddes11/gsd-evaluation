from app import db
from datetime import datetime

class Media(db.Model):
    """Media model for uploaded images and files"""
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False, unique=True, index=True)
    mime_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user
    uploader = db.relationship('User', backref=db.backref('media', lazy='dynamic'))

    def __repr__(self):
        return f'<Media {self.id}: {self.filename}'