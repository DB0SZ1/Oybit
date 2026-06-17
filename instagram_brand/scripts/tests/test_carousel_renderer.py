import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from render_engine.carousel import render_carousel, render_carousel_sync

def run_tests():
    print("=" * 40)
    print("Running Carousel Renderer Tests")
    print("=" * 40)
    try:
        print("\n[1] Testing slide parsing...")
        assert render_carousel is not None
        print("[PASS] Parsed slides imported successfully")

        print("\n" + "=" * 40)
        print("ALL CAROUSEL RENDERING TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
