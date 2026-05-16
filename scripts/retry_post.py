"""
Oybit Operations — Retry a failed post by ID.
Usage: python scripts/retry_post.py <post_id> [--dry-run]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def retry_post(post_id: int, dry_run: bool = False):
    """Retry a failed post by resetting its status and re-dispatching."""
    from dotenv import load_dotenv
    load_dotenv()

    from backend.db.session import get_session
    from backend.db.models import Post
    from backend.publishers.dispatcher import dispatch

    db = get_session()
    try:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            print(f"❌ Post {post_id} not found")
            return

        print(f"Post {post_id}:")
        print(f"  Account: {post.account}")
        print(f"  Status: {post.status}")
        print(f"  Format: {post.format}")
        print(f"  Content: {(post.content_text or '')[:100]}...")

        if post.status == "published":
            print(f"⚠️  Post is already published — skipping")
            return

        if dry_run:
            print(f"[DRY RUN] Would reset status to 'pending' and re-dispatch")
            return

        # Reset status
        post.status = "pending"
        post.last_error = None
        db.commit()
        print(f"✅ Status reset to 'pending'")

        # Re-dispatch
        post_data = {
            "post_id": post.id,
            "format": post.format,
            "content_text": post.content_text,
            "media_urls": post.media_urls or [],
        }

        result = dispatch(post_data, account=post.account)
        print(f"Dispatch result: {result}")

    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/retry_post.py <post_id> [--dry-run]")
        sys.exit(1)

    post_id = int(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    retry_post(post_id, dry_run=dry_run)


if __name__ == "__main__":
    main()
