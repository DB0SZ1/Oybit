"""
Oybit Operations — Force token refresh for a specific account.
Usage: python scripts/refresh_token.py <account_name>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def refresh_meta_token(account: str):
    """Force refresh a Meta long-lived token."""
    import httpx
    from dotenv import load_dotenv
    load_dotenv()

    token_map = {
        "instagram_personal": "INSTAGRAM_PERSONAL_TOKEN",
        "instagram_brand": "INSTAGRAM_BRAND_TOKEN",
        "facebook": "FACEBOOK_PAGE_TOKEN",
    }

    env_var = token_map.get(account)
    if not env_var:
        print(f"❌ Unknown account: {account}")
        print(f"   Valid: {', '.join(token_map.keys())}")
        return

    current_token = os.getenv(env_var, "")
    if not current_token:
        print(f"❌ {env_var} is not set")
        return

    app_id = os.getenv("FACEBOOK_APP_ID", "")
    app_secret = os.getenv("FACEBOOK_APP_SECRET", "")
    if not app_id or not app_secret:
        print("❌ FACEBOOK_APP_ID and FACEBOOK_APP_SECRET required")
        return

    version = os.getenv("META_GRAPH_API_VERSION", "v19.0")

    try:
        resp = httpx.get(
            f"https://graph.facebook.com/{version}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": current_token,
            },
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            new_token = data.get("access_token", "")
            expires_in = data.get("expires_in", 0)
            days = expires_in // 86400

            print(f"✅ Token refreshed for {account}")
            print(f"   Expires in: {days} days")
            print(f"\n   Update your .env:")
            print(f"   {env_var}={new_token[:20]}...{new_token[-10:]}")
            print(f"\n   Full token (copy this):")
            print(f"   {new_token}")
        else:
            print(f"❌ Refresh failed: {resp.text[:300]}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/refresh_token.py <account_name>")
        print("  Accounts: instagram_personal, instagram_brand, facebook")
        sys.exit(1)

    account = sys.argv[1]
    refresh_meta_token(account)


if __name__ == "__main__":
    main()
