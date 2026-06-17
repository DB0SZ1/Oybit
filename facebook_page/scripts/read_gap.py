import sys
import re
from pathlib import Path

def get_gap_content(gap_id):
    files = ['GAPS_AND_FIXES.md', 'OYBIT_GAP_SOLUTIONS.md', 'GAPS_FINAL.md']
    for f in files:
        content = Path(f).read_text(encoding='utf-8')
        # match ## GAP <gap_id> — TITLE ... until next ## GAP
        # Use regex to find it
        pattern = r'(##\s*GAP\s*' + re.escape(gap_id) + r'\s*—.*?)(?=\n##\s*GAP|\Z)'
        match = re.search(pattern, content, flags=re.DOTALL)
        if match:
            print(f"--- FOUND IN {f} ---")
            print(match.group(1).strip())
            return
            
    print(f"Gap {gap_id} not found.")

if __name__ == "__main__":
    get_gap_content(sys.argv[1])
