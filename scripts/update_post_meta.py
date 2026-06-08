"""
Update published_at and view count metadata by post_id

Usage:
    python scripts/update_post_meta.py <post_id> <published_at> <view_count>

Arguments:
    post_id         integer id of the post
    published_at    datetime string "2024-03-15" or "2025-01-01 14:30:00"
    view_count      integer view count

Examples:
    python scripts/update_post_meta.py 1 "2024-03-01" 1234

Run from container:
    docker compose exec blog python scripts/update_post_meta.py 1 "2024-03-01" 1234
"""

import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.post import Post

DATETIME_FORMATS = {
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
}

def parse_datetime(value):
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: '{value}'")

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    try:
        post_id = int(sys.argv[1])
        published_at = parse_datetime(sys.argv[2])
        view_count = int(sys.argv[3])
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    app = create_app("ProductionConfig")
    with app.app_context():
        post = Post.query.get(post_id)
        if not post:
            print(f"Error: no post found with ID {post_id}")
            sys.exit(1)
        post.published_at = published_at
        post.view_count = view_count
        db.session.commit()

        print(f"Update post {post_id} '{post.title}':")
        print(f"  published_at: {post.published_at}")
        print(f"  view_count: {post.view_count}")

if __name__ == "__main__":
    main()
