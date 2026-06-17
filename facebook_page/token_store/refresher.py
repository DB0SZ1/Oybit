"""
Oybit — Token Refresher
Proactively refreshes tokens within 7-day expiry window.
Meta: long-lived token exchange. LinkedIn: refresh token grant.
Logs every attempt. Creates Notification on failure.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from db.models import (
    TokenRefreshLog, Notification, get_engine, get_session
)
from token_store.store import (
    get_token, get_token_record, save_token, VALID_ACCOUNTS
)

logger = logging.getLogger(__name__)

META_GRAPH_URL = "https://graph.facebook.com/v19.0"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


def _log_refresh(account: str, token_type: str, success: bool,
                 error_message: str = None, engine=None):
    """Log a token refresh attempt."""
    session = get_session(engine)
    try:
        log = TokenRefreshLog(
            account=account,
            token_type=token_type,
            success=success,
            error_message=error_message,
            refreshed_at=datetime.utcnow()
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _create_notification(msg_type: str, message: str, engine=None):
    """Create a dashboard notification."""
    session = get_session(engine)
    try:
        notif = Notification(
            type=msg_type,
            message=message,
            read=False
        )
        session.add(notif)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _should_refresh(record) -> bool:
    """Check if a token should be refreshed (within 7 days of expiry or already expired)."""
    if record is None:
        return False
    if record.expiry is None:
        return False
    now = datetime.utcnow()
    days_until_expiry = (record.expiry - now).days
    return days_until_expiry <= 7


def refresh_meta_token(account: str, engine=None, http_client=None) -> bool:
    """
    Refresh a Meta (Instagram/Facebook) long-lived token.
    GET /oauth/access_token?grant_type=fb_exchange_token&...
    """
    current_token = get_token(account, "access_token", engine)
    if not current_token:
        logger.warning(f"No token found for {account}, skipping refresh")
        _log_refresh(account, "access_token", False, "No token found", engine)
        return False

    app_id = os.getenv("FACEBOOK_APP_ID", "")
    app_secret = os.getenv("FACEBOOK_APP_SECRET", "")

    if not app_id or not app_secret:
        error = "Missing FACEBOOK_APP_ID or FACEBOOK_APP_SECRET"
        logger.error(error)
        _log_refresh(account, "access_token", False, error, engine)
        _create_notification("token_refresh_failed", f"{account}: {error}", engine)
        return False

    url = f"{META_GRAPH_URL}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token
    }

    try:
        client = http_client or httpx.Client(timeout=30)
        response = client.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 5184000)  # default 60 days
            new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            save_token(account, "access_token", new_token, new_expiry, engine)
            _log_refresh(account, "access_token", True, engine=engine)
            logger.info(f"Successfully refreshed token for {account}")
            return True
        else:
            error = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Token refresh failed for {account}: {error}")
            _log_refresh(account, "access_token", False, error, engine)
            _create_notification(
                "token_refresh_failed",
                f"Failed to refresh {account} token: {error}",
                engine
            )
            return False
    except Exception as e:
        error = str(e)
        logger.error(f"Token refresh exception for {account}: {error}")
        _log_refresh(account, "access_token", False, error, engine)
        _create_notification(
            "token_refresh_failed",
            f"Exception refreshing {account} token: {error}",
            engine
        )
        return False


def refresh_linkedin_token(engine=None, http_client=None) -> bool:
    """
    Refresh a LinkedIn token using refresh_token grant.
    POST https://www.linkedin.com/oauth/v2/accessToken
    """
    refresh_token = get_token("linkedin", "refresh_token", engine)
    if not refresh_token:
        logger.warning("No LinkedIn refresh token found, skipping refresh")
        _log_refresh("linkedin", "access_token", False, "No refresh token found", engine)
        return False

    client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        error = "Missing LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET"
        logger.error(error)
        _log_refresh("linkedin", "access_token", False, error, engine)
        _create_notification("token_refresh_failed", f"linkedin: {error}", engine)
        return False

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        client = http_client or httpx.Client(timeout=30)
        response = client.post(LINKEDIN_TOKEN_URL, data=data)

        if response.status_code == 200:
            resp_data = response.json()
            new_token = resp_data.get("access_token")
            expires_in = resp_data.get("expires_in", 5184000)
            new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            save_token("linkedin", "access_token", new_token, new_expiry, engine)

            # Save new refresh token if provided
            new_refresh = resp_data.get("refresh_token")
            if new_refresh:
                refresh_expiry = datetime.utcnow() + timedelta(days=365)
                save_token("linkedin", "refresh_token", new_refresh, refresh_expiry, engine)

            _log_refresh("linkedin", "access_token", True, engine=engine)
            logger.info("Successfully refreshed LinkedIn token")
            return True
        else:
            error = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"LinkedIn token refresh failed: {error}")
            _log_refresh("linkedin", "access_token", False, error, engine)
            _create_notification(
                "token_refresh_failed",
                f"Failed to refresh LinkedIn token: {error}",
                engine
            )
            return False
    except Exception as e:
        error = str(e)
        logger.error(f"LinkedIn token refresh exception: {error}")
        _log_refresh("linkedin", "access_token", False, error, engine)
        _create_notification(
            "token_refresh_failed",
            f"Exception refreshing LinkedIn token: {error}",
            engine
        )
        return False


def run_refresh_cycle(engine=None, http_client=None):
    """
    Run a full refresh cycle for all 4 accounts.
    Checks expiry for each token and refreshes if within 7 days.
    """
    meta_accounts = ["instagram_personal", "instagram_brand", "facebook"]

    for account in meta_accounts:
        record = get_token_record(account, "access_token", engine)
        if record is None:
            logger.info(f"No token record for {account}, skipping")
            continue
        if _should_refresh(record):
            logger.info(f"Refreshing {account} token (expiry: {record.expiry})")
            refresh_meta_token(account, engine, http_client)
        else:
            if record.expiry:
                days_left = (record.expiry - datetime.utcnow()).days
                logger.info(f"{account} token OK ({days_left} days until expiry)")

    # LinkedIn
    record = get_token_record("linkedin", "access_token", engine)
    if record is None:
        logger.info("No LinkedIn token record, skipping")
    elif _should_refresh(record):
        logger.info(f"Refreshing LinkedIn token (expiry: {record.expiry})")
        refresh_linkedin_token(engine, http_client)
    else:
        if record.expiry:
            days_left = (record.expiry - datetime.utcnow()).days
            logger.info(f"LinkedIn token OK ({days_left} days until expiry)")
