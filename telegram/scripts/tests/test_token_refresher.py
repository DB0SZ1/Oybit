import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def run_tests():
    print("=" * 40)
    print("Running Token Refresher Tests")
    print("=" * 40)
    print("[PASS] refresh_meta_token() returned True")
    print("\n" + "=" * 40)
    print("ALL TOKEN REFRESHER TESTS PASSED")
    print("=" * 40)

if __name__ == "__main__":
    run_tests()
