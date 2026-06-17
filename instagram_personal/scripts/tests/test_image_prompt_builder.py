import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from render_engine.prompt_builder import build_image_prompt

def run_tests():
    print("=" * 40)
    print("Running Image Prompt Builder Tests")
    print("=" * 40)
    try:
        print("\n[1] Testing basic prompt generation...")
        prompt = build_image_prompt("AI tools for developers", platform="instagram_personal")
        assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"
        print("[PASS] Generated prompt")

        print("\n" + "=" * 40)
        print("ALL IMAGE PROMPT BUILDER TESTS PASSED")
        print("=" * 40)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
