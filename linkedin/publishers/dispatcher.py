"""
Oybit — Publisher Dispatcher
Routes posts to correct publisher(s) based on account field.
"""
import logging
import asyncio

from publishers.linkedin import publish_to_linkedin

logger = logging.getLogger(__name__)

def dispatch(post_data: dict, account: str = None, accounts: list[str] = None,
             dry_run: bool = False) -> dict:
    """
    Dispatch a post to one or more publishers.
    """
    target_accounts = []
    if accounts:
        target_accounts = accounts
    elif account:
        target_accounts = [account]
    else:
        # Default to the account in post_data
        target_accounts = [post_data.get("account", "linkedin")]

    if not target_accounts or not target_accounts[0]:
        raise ValueError("No target account specified for dispatch")

    results = {}
    for acct in target_accounts:
        if acct != "linkedin":
            results[acct] = {"success": False, "error": f"Unknown or unsupported account: {acct}"}
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

            if dry_run:
                results[acct] = {"success": True, "dry_run": True, "platform_post_id": "dry_run_id"}
                continue

            # Publish to LinkedIn synchronously by wrapping the async function
            content_text = post_data.get("content_text", "")
            media_urls = post_data.get("media_urls", [])
            format_type = post_data.get("format", "text")
            
            result = asyncio.run(publish_to_linkedin(
                content_text=content_text,
                media_paths=media_urls if media_urls else None,
                format_type=format_type
            ))
            results[acct] = result
        except Exception as e:
            logger.error(f"Dispatch to {acct} failed: {e}")
            results[acct] = {"success": False, "error": str(e), "account": acct}

    return results
