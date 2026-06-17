"""
Oybit Operations — Check token expiry dates.
Usage: python scripts/check_tokens.py [--dry-run]
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_meta_token_expiry() -> list:
    """Check Meta token debug info for expiry dates."""
    import httpx

    tokens = {
        "instagram_personal": os.getenv("INSTAGRAM_PERSONAL_TOKEN", ""),
        "instagram_brand": os.getenv("INSTAGRAM_BRAND_TOKEN", ""),
        "facebook_page": os.getenv("FACEBOOK_PAGE_TOKEN", ""),
    }

    app_token = f"{os.getenv('FACEBOOK_APP_ID', '')}|{os.getenv('FACEBOOK_APP_SECRET', '')}"
    results = []

    for name, token in tokens.items():
        if not token:
            results.append({"account": name, "status": "missing"})
            continue

        try:
            resp = httpx.get(
                "https://graph.facebook.com/debug_token",
                params={"input_token": token, "access_token": app_token},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                expires_at = data.get("expires_at", 0)
                if expires_at == 0:
                    expiry_str = "never (long-lived)"
                    days_left = 999
                else:
                    expiry = datetime.utcfromtimestamp(expires_at)
                    days_left = (expiry - datetime.utcnow()).days
                    expiry_str = expiry.strftime("%Y-%m-%d %H:%M UTC")

                results.append({
                    "account": name,
                    "status": "ok",
                    "expires": expiry_str,
                    "days_left": days_left,
                    "scopes": data.get("scopes", []),
                    "is_valid": data.get("is_valid", False),
                })
            else:
                results.append({"account": name, "status": "check_failed", "error": resp.text[:200]})
        except Exception as e:
            results.append({"account": name, "status": "error", "error": str(e)})

    return results


def main():
    from dotenv import load_dotenv
    load_dotenv()

    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Oybit — Token Expiry Check")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN] Listing configured tokens\n")
        token_vars = [
            "INSTAGRAM_PERSONAL_TOKEN", "INSTAGRAM_BRAND_TOKEN",
            "FACEBOOK_PAGE_TOKEN", "LINKEDIN_ACCESS_TOKEN",
            "OPENROUTER_API_KEY", "REDDIT_CLIENT_ID",
        ]
        for var in token_vars:
            val = os.getenv(var, "")
            status = f"set ({len(val)} chars)" if val else "MISSING"
            icon = "✅" if val else "❌"
            print(f"  {icon} {var}: {status}")
        return

    print("\nMeta Tokens:")
    results = check_meta_token_expiry()
    for r in results:
        if r["status"] == "ok":
            days = r["days_left"]
            icon = "✅" if days > 14 else "⚠️" if days > 3 else "🚨"
            print(f"  {icon} {r['account']}: expires {r['expires']} ({days} days)")
            print(f"     └─ valid: {r['is_valid']} | scopes: {len(r['scopes'])}")
        elif r["status"] == "missing":
            print(f"  ⚠️  {r['account']}: not configured")
        else:
            print(f"  ❌ {r['account']}: {r.get('error', 'unknown error')}")

    # LinkedIn doesn't have a debug endpoint — just check validity
    print("\nLinkedIn: use verify_connections.py to test")
    print("\nOpenRouter: use verify_connections.py to test")


if __name__ == "__main__":
    main()
