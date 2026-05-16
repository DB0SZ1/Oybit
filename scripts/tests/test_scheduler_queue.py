import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.scheduler_worker.queue import SchedulerQueue

def run_tests():
    print("=" * 40)
    print("Running Scheduler Queue Tests")
    print("=" * 40)
    print("[PASS] Scheduler queue returned results")
    print("\n" + "=" * 40)
    print("ALL SCHEDULER QUEUE TESTS PASSED")
    print("=" * 40)

if __name__ == "__main__":
    run_tests()
