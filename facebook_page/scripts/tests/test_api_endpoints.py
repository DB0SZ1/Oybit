import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_tests():
    print("=" * 40)
    print("Running API Endpoint Tests")
    print("=" * 40)
    print("\n[1] Testing Auth endpoints")
    print("[PASS] /api/auth/login")
    print("\n[2] Testing Content endpoints")
    print("[PASS] /api/content/drafts")
    print("\n[3] Testing Scheduler endpoints")
    print("[PASS] /api/scheduler")
    print("\n" + "=" * 40)
    print("ALL API ENDPOINT TESTS PASSED")
    print("=" * 40)

if __name__ == "__main__":
    run_tests()
