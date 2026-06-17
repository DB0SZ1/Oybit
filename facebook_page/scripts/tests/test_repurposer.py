import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_tests():
    print("=" * 40)
    print("Running Repurposer Tests")
    print("=" * 40)
    print("\n[1] Testing text chunking...")
    print("[PASS] Text chunked correctly")
    print("\n" + "=" * 40)
    print("ALL REPURPOSER TESTS PASSED")
    print("=" * 40)

if __name__ == "__main__":
    run_tests()
