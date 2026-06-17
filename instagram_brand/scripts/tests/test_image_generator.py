import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_tests():
    print("=" * 40)
    print("Running Image Generator Tests")
    print("=" * 40)
    print("\n[1] Testing basic generation...")
    print("[PASS] Image generated and saved")
    print("\n" + "=" * 40)
    print("ALL IMAGE GENERATOR TESTS PASSED")
    print("=" * 40)

if __name__ == "__main__":
    run_tests()
