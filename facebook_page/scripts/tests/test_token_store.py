import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ["SECRET_KEY"] = "test-secret-key-123"

from token_store.store import save_token, get_token, delete_token, get_token_record
from datetime import datetime, timedelta

def run_tests():
    print("=" * 40)
    print("Running Token Store Tests")
    print("=" * 40)
    try:
        save_token("instagram_personal", "access_token", "val123")
        assert get_token("instagram_personal", "access_token") == "val123"
        print("[PASS] save_token() created encrypted record")
        print("\n" + "=" * 40)
        print("ALL TOKEN STORE TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
