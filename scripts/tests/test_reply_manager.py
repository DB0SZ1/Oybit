import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.reply_manager.monitor import classify_comment

def run_tests():
    print("=" * 40)
    print("Running Reply Manager Tests")
    print("=" * 40)
    try:
        assert classify_comment("Great post!") == "praise"
        print("[PASS] Comment classified as praise")
        print("\n" + "=" * 40)
        print("ALL REPLY MANAGER TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
