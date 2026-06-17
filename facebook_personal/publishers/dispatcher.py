"""
Oybit — Publisher Dispatcher
Routes posts to correct publisher(s) based on account field.
Handles cross-posting (same post to multiple accounts).
"""
import logging

from publishers.instagram_personal import InstagramPersonalPublisher
from publishers.instagram_brand import InstagramBrandPublisher
from publishers.facebook import FacebookPublisher
from publishers.linkedin import LinkedInPublisher

logger = logging.getLogger(__name__)

PUBLISHER_MAP = {
    "instagram_personal": InstagramPersonalPublisher,
    "instagram_brand": InstagramBrandPublisher,
    "facebook": FacebookPublisher,
    "linkedin": LinkedInPublisher,
}


def dispatch(post_data: dict, account: str = None, accounts: list[str] = None,
             dry_run: bool = False) -> dict:
    """
    Dispatch a post to one or more publishers.

    Args:
        post_data: dict with format, content_text, media_urls
        account: single account name (e.g. "instagram_personal")
        accounts: list of account names for cross-posting
        dry_run: if True, validate payload but don't actually post

    Returns:
        dict with per-account results: {account_name: {success/failure details}}
    """
    target_accounts = []
    if accounts:
        target_accounts = accounts
    elif account:
        target_accounts = [account]
    else:
        # Default to the account in post_data
        target_accounts = [post_data.get("account", "")]

    if not target_accounts or not target_accounts[0]:
        raise ValueError("No target account specified for dispatch")

    results = {}
    for acct in target_accounts:
        if acct not in PUBLISHER_MAP:
            results[acct] = {"success": False, "error": f"Unknown account: {acct}"}
            continue

        try:
            # Idempotency lock via database if post is defined
            post_id = post_data.get("post_id")
            if post_id:
                from db.session import SessionLocal
                from sqlalchemy import text
                from db.models import Post
                from utils.exceptions import PostAlreadyPublishedError
                db = SessionLocal()
                try:
                    post = db.query(Post).filter_by(id=post_id).first()
                    if post and post.status == "published":
                        logger.warning({"event": "duplicate_publish_prevented", "post_id": post_id})
                        raise PostAlreadyPublishedError(f"Post {post_id} already published")

                    # Advisory lock (skip if using SQLite locally for testing)
                    if "sqlite" not in str(db.get_bind().url):
                        db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": post_id})
                        db.refresh(post)
                        if post and post.status == "published":
                            raise PostAlreadyPublishedError(f"Post {post_id} already published (race condition caught)")
                finally:
                    db.close()

            publisher_class = PUBLISHER_MAP[acct]
            publisher = publisher_class(dry_run=dry_run)
            result = publisher.publish(post_data)
            results[acct] = result
        except Exception as e:
            logger.error(f"Dispatch to {acct} failed: {e}")
            results[acct] = {"success": False, "error": str(e), "account": acct}

    return results
