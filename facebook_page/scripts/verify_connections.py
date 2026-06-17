"""
Oybit Operations — Verify all platform connections.
Usage: python scripts/verify_connections.py [--dry-run]
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_meta_tokens() -> dict:
    """Verify Meta/Instagram tokens are valid."""
    import httpx
    results = {}

    accounts = {
        "instagram_personal": os.getenv("INSTAGRAM_PERSONAL_TOKEN", ""),
        "instagram_brand": os.getenv("INSTAGRAM_BRAND_TOKEN", ""),
        "facebook_page": os.getenv("FACEBOOK_PAGE_TOKEN", ""),
    }

    meta_version = os.getenv("META_GRAPH_API_VERSION", "v19.0")

    for name, token in accounts.items():
        if not token:
            results[name] = {"status": "missing", "error": "Token not set"}
            continue

        try:
            resp = httpx.get(
                f"https://graph.facebook.com/{meta_version}/me",
                params={"access_token": token},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                results[name] = {"status": "ok", "user_id": data.get("id"), "name": data.get("name", "")}
            else:
                results[name] = {"status": "failed", "error": resp.text[:200]}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    return results


def check_linkedin_token() -> dict:
    """Verify LinkedIn token is valid."""
    import httpx
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        return {"status": "missing", "error": "Token not set"}

    try:
        resp = httpx.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"status": "ok", "name": data.get("name", ""), "sub": data.get("sub", "")}
        else:
            return {"status": "failed", "error": resp.text[:200]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_openrouter() -> dict:
    """Verify OpenRouter API key works."""
    import httpx
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        return {"status": "missing", "error": "API key not set"}

    try:
        resp = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            return {"status": "ok", "models_available": len(models)}
        else:
            return {"status": "failed", "error": resp.text[:200]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_reddit() -> dict:
    """Verify Reddit API access."""
    import httpx
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    if not client_id:
        return {"status": "missing", "error": "Client ID not set"}

    try:
        resp = httpx.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": "Oybit/1.0"},
            timeout=10,
        )
        if resp.status_code == 200:
            return {"status": "ok", "token_type": resp.json().get("token_type")}
        else:
            return {"status": "failed", "error": resp.text[:200]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    from dotenv import load_dotenv
    load_dotenv()

    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Oybit — Platform Connection Verification")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN] Checking env vars only\n")
        checks = {
            "OPENROUTER_API_KEY": bool(os.getenv("OPENROUTER_API_KEY")),
            "INSTAGRAM_PERSONAL_TOKEN": bool(os.getenv("INSTAGRAM_PERSONAL_TOKEN")),
            "INSTAGRAM_BRAND_TOKEN": bool(os.getenv("INSTAGRAM_BRAND_TOKEN")),
            "FACEBOOK_PAGE_TOKEN": bool(os.getenv("FACEBOOK_PAGE_TOKEN")),
            "LINKEDIN_ACCESS_TOKEN": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            "REDDIT_CLIENT_ID": bool(os.getenv("REDDIT_CLIENT_ID")),
            "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        }
        for key, present in checks.items():
            icon = "✅" if present else "❌"
            print(f"  {icon} {key}: {'set' if present else 'MISSING'}")
        return

    checks = [
        ("Meta (Instagram + Facebook)", check_meta_tokens),
        ("LinkedIn", check_linkedin_token),
        ("OpenRouter AI", check_openrouter),
        ("Reddit", check_reddit),
    ]

    all_ok = True
    for name, check_fn in checks:
        print(f"\n{name}:")
        result = check_fn()
        if isinstance(result, dict) and "status" in result:
            results = {name: result}
        else:
            results = result

        for key, val in results.items():
            status = val.get("status", "unknown")
            icon = "✅" if status == "ok" else "⚠️" if status == "missing" else "❌"
            print(f"  {icon} {key}: {status}")
            if status != "ok":
                print(f"     └─ {val.get('error', '')}")
                all_ok = False

    print(f"\n{'=' * 50}")
    print(f"Result: {'ALL OK ✅' if all_ok else 'ISSUES FOUND ❌'}")


if __name__ == "__main__":
    main()
