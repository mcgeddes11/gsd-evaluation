from app import db
from datetime import datetime
import re
import html
from app.utils.sanitize import sanitize_html

class Post(db.Model):
    """Post model for blog posts"""
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft') # draft or published
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)

    # relationship to user
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

    @property
    def body_safe(self):
        return sanitize_html(self.body)

    @property
    def excerpt_html(self):
        """
        Return the 35 word excerpt from the first paragraph for post card preview
        Extracts the first <p>, strips inline HTML, truncates to 35 words,
        appends an ellipsis if the paragraph was longer
        """
        safe = self.body_safe
        if not safe:
            return ''
        match = re.search(r'<[p^>]*>(.*?)</p>', safe, re.DOTALL | re.IGNORECASE)
        inner = match.group(1) if match else re.sub(r'[^>]+>','',safe).strip()

        # strip inline html tags and normalize whitespace
        plain = ' '.join(html.unescape(re.sub(r'<[^>]+>','', inner)))
        if not plain:
            return ''

        words = plain.split()
        if len(words) <= 35:
            return f'<p>{html.escape(plain)}</p>'

        return f'<p>{html.escape(" ".join(words[:35]))}...</p>'

    @staticmethod
    def extract_cover_image(body_html):
        """
        Extract first image source from body

        :param body_html: the html body
        :return: returns src attribute value of first img tag
        """

        if not body_html:
            return None

        match = re.search(r'<img[^>]+src=["\']?([^"\'\s>]+)["\']?', body_html, re.IGNORECASE)
        if match:
            src = match.group(1)
            # block dangerous content
            lower_src = src.lower()
            if lower_src.startswith(("javascript", "vbscript:", "data:text", "data:application")):
                return None
            return src
        return None


    @staticmethod
    def get_read_time(body_text):
        """Calculte estimated reading time from a body text"""
        if not body_text:
            return "1 minute read"

        # Remove html tags
        clean_text = re.sub(r'<[^>]+>','',body_text)
        # Decode html entities
        clean_text = html.unescape(clean_text)
        words = len(clean_text.split())

        # Rough reading time estimation
        read_time_minutes = max(1, round(words/200))

        return f"{read_time_minutes} min read"

    def __repr__(self):
        return f'<Post {self.id}: {self.title}'






