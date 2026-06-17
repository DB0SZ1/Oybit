import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

os.environ["SECRET_KEY"] = "test-secret-key-123"
os.environ["INSTAGRAM_PERSONAL_ACCESS_TOKEN"] = "test_ig_pers_token"
os.environ["INSTAGRAM_PERSONAL_USER_ID"] = "12345"

from publishers.instagram_personal import InstagramPersonalPublisher
from publishers.dispatcher import dispatch

def run_tests():
    print("=" * 40)
    print("Running Publisher Tests")
    print("=" * 40)

    try:
        print("\n[1] Testing InstagramPersonalPublisher dry_run...")
        pub = InstagramPersonalPublisher(dry_run=True)
        result = pub.publish_single_image("https://example.com/img.jpg", "Test caption")
        assert result["dry_run"] is True
        print("[PASS] IG Personal single image dry_run")

        print("\n" + "=" * 40)
        print("ALL PUBLISHER TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
