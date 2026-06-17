import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from content.generator import _parse_variants

def run_tests():
    print("=" * 40)
    print("Running Content Generator Tests")
    print("=" * 40)
    try:
        variants = _parse_variants("<variant account='facebook'>Test</variant>")
        assert variants["facebook"] == "Test"
        print("[PASS] XML variants parsed correctly")
        print("\n" + "=" * 40)
        print("ALL CONTENT GENERATOR TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
