"""
Oybit — Token Store
Encrypted storage for all 4 account tokens in PostgreSQL.
Uses Fernet symmetric encryption with SECRET_KEY from env.
"""
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib

from db.models import TokenRecord, get_engine, get_session, create_all_tables


VALID_ACCOUNTS = ["instagram_personal", "instagram_brand", "facebook", "linkedin"]
VALID_TOKEN_TYPES = ["access_token", "refresh_token"]


def _get_fernet() -> Fernet:
    """Get Fernet cipher using SECRET_KEY from env."""
    secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    # Derive a 32-byte key from SECRET_KEY using SHA-256, then base64 encode
    key_bytes = hashlib.sha256(secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def save_token(account: str, token_type: str, value: str, expiry: datetime = None,
               engine=None) -> TokenRecord:
    """
    Save or update an encrypted token for an account.
    If a record with the same account+token_type exists, it is updated (not duplicated).
    """
    if account not in VALID_ACCOUNTS:
        raise ValueError(f"Invalid account: {account}. Must be one of {VALID_ACCOUNTS}")
    if token_type not in VALID_TOKEN_TYPES:
        raise ValueError(f"Invalid token_type: {token_type}. Must be one of {VALID_TOKEN_TYPES}")

    fernet = _get_fernet()
    encrypted = fernet.encrypt(value.encode()).decode()

    session = get_session(engine)
    try:
        # Check if record exists
        existing = session.query(TokenRecord).filter_by(
            account=account, token_type=token_type
        ).first()

        if existing:
            existing.encrypted_value = encrypted
            existing.expiry = expiry
            existing.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(existing)
            return existing
        else:
            record = TokenRecord(
                account=account,
                token_type=token_type,
                encrypted_value=encrypted,
                expiry=expiry
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_token(account: str, token_type: str, engine=None) -> str | None:
    """
    Get a decrypted token value for an account.
    Returns None if not found.
    """
    session = get_session(engine)
    try:
        record = session.query(TokenRecord).filter_by(
            account=account, token_type=token_type
        ).first()

        if record is None:
            return None

        fernet = _get_fernet()
        return fernet.decrypt(record.encrypted_value.encode()).decode()
    finally:
        session.close()


def get_token_record(account: str, token_type: str, engine=None) -> TokenRecord | None:
    """
    Get the full TokenRecord for an account (including expiry).
    Returns None if not found.
    """
    session = get_session(engine)
    try:
        record = session.query(TokenRecord).filter_by(
            account=account, token_type=token_type
        ).first()
        return record
    finally:
        session.close()


def delete_token(account: str, token_type: str, engine=None) -> bool:
    """
    Delete a token record. Returns True if deleted, False if not found.
    """
    session = get_session(engine)
    try:
        record = session.query(TokenRecord).filter_by(
            account=account, token_type=token_type
        ).first()

        if record is None:
            return False

        session.delete(record)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_tokens(engine=None) -> list[TokenRecord]:
    """Get all token records (for refresher to iterate over)."""
    session = get_session(engine)
    try:
        return session.query(TokenRecord).all()
    finally:
        session.close()
