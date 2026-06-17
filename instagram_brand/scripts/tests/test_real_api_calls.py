"""
Real API Call Tests — GAP 5.2
ONLY run these manually — they hit real platform APIs.
Run: python scripts/tests/test_real_api_calls.py --real-apis

Requirements:
- Valid tokens for all 4 accounts in .env
- Instagram Personal and Brand accounts connected
- LinkedIn account connected
- Facebook page connected
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if "--real-apis" not in sys.argv:
    print("⏭ Skipping real API tests. Add --real-apis flag to run.")
    sys.exit(0)

try:
    import requests
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ Missing dependencies: pip install requests python-dotenv")
    sys.exit(1)


def test_instagram_personal_token_valid():
    """Verify personal IG token works and account is reachable."""
    token = os.getenv("INSTAGRAM_PERSONAL_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_PERSONAL_USER_ID")
    if not token or not user_id:
        print("  ⚠ INSTAGRAM_PERSONAL_ACCESS_TOKEN or USER_ID not set — skipping")
        return

    response = requests.get(
        f"https://graph.facebook.com/v19.0/{user_id}",
        params={"fields": "id,username,followers_count", "access_token": token},
        timeout=15,
    )
    data = response.json()
    assert "error" not in data, f"Token invalid: {data}"
    assert "id" in data, "No ID in response"
    print(f"  ✅ Instagram Personal — @{data.get('username')} ({data.get('followers_count')} followers)")


def test_instagram_brand_token_valid():
    """Verify brand IG token is still active."""
    token = os.getenv("INSTAGRAM_BRAND_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_BRAND_USER_ID")
    if not token or not user_id:
        print("  ⚠ INSTAGRAM_BRAND tokens not set — skipping")
        return

    response = requests.get(
        f"https://graph.facebook.com/v19.0/{user_id}",
        params={"fields": "id,username,followers_count", "access_token": token},
        timeout=15,
    )
    data = response.json()
    assert "error" not in data, f"Token invalid: {data}"
    print(f"  ✅ Instagram Brand — @{data.get('username')} ({data.get('followers_count')} followers)")


def test_linkedin_token_valid():
    """Verify LinkedIn token is valid."""
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        print("  ⚠ LINKEDIN_ACCESS_TOKEN not set — skipping")
        return

    response = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = response.json()
    assert response.status_code == 200, f"LinkedIn token invalid: {data}"
    print(f"  ✅ LinkedIn — {data.get('localizedFirstName')} {data.get('localizedLastName')}")


def test_facebook_page_token_valid():
    """Verify Facebook page token."""
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not token or not page_id:
        print("  ⚠ FACEBOOK_PAGE tokens not set — skipping")
        return

    response = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}",
        params={"fields": "id,name,fan_count", "access_token": token},
        timeout=15,
    )
    data = response.json()
    assert "error" not in data, f"Facebook token invalid: {data}"
    print(f"  ✅ Facebook Page — {data.get('name')} ({data.get('fan_count')} fans)")


def test_openrouter_real_call():
    """Make one real OpenRouter call with a simple prompt."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("  ⚠ OPENROUTER_API_KEY not set — skipping")
        return

    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://oybit.nyvora.com",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: TEST_OK"}],
            "max_tokens": 10,
        },
        timeout=30,
    )
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    assert "TEST_OK" in content, f"Unexpected response: {content}"
    print(f"  ✅ OpenRouter call succeeded — model: {model}")


if __name__ == "__main__":
    print("\n🌐 Real API Call Tests\n" + "=" * 50)
    print("⚠ These tests hit REAL platform APIs!\n")

    tests = [
        ("Instagram Personal token", test_instagram_personal_token_valid),
        ("Instagram Brand token", test_instagram_brand_token_valid),
        ("LinkedIn token", test_linkedin_token_valid),
        ("Facebook Page token", test_facebook_page_token_valid),
        ("OpenRouter API", test_openrouter_real_call),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            print(f"\n▶ {name}")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
