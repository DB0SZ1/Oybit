import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from analytics.aggregator import compute_engagement_score

def run_tests():
    print("=" * 40)
    print("Running Analytics Aggregator Tests")
    print("=" * 40)
    try:
        assert compute_engagement_score(saves=2, shares=1, comments=1, follows=0) == 15
        print("[PASS] Engagement score correctly computed")
        print("\n" + "=" * 40)
        print("ALL ANALYTICS AGGREGATOR TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
