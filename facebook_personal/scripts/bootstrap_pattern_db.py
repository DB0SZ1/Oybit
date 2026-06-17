"""
Oybit — bootstrap_pattern_db.py (GAPS_FINAL GAP 7.3)
Seeds the PatternDB with initial patterns from LinkedIn history or defaults.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_session
from db.models import PatternDB
from datetime import datetime

DEFAULT_PATTERNS = [
    {"pattern_name": "question", "success_metric": 6.5, "trigger_conditions": {"format": "text", "starts_with": "question"}},
    {"pattern_name": "contrarian", "success_metric": 7.2, "trigger_conditions": {"format": "text", "tone": "provocative"}},
    {"pattern_name": "how_to", "success_metric": 6.0, "trigger_conditions": {"format": "carousel", "educational": True}},
    {"pattern_name": "story", "success_metric": 7.8, "trigger_conditions": {"format": "text", "personal": True}},
    {"pattern_name": "listicle", "success_metric": 5.5, "trigger_conditions": {"format": "carousel", "numbered": True}},
    {"pattern_name": "statement", "success_metric": 5.0, "trigger_conditions": {"format": "text", "generic": True}},
    {"pattern_name": "behind_the_scenes", "success_metric": 8.0, "trigger_conditions": {"format": "reel", "authentic": True}},
    {"pattern_name": "data_insight", "success_metric": 6.8, "trigger_conditions": {"format": "image", "data_driven": True}},
]

def main():
    db = get_session()
    
    existing = db.query(PatternDB).count()
    if existing > 0:
        print(f"[INFO] PatternDB already has {existing} patterns. Skipping bootstrap.")
        db.close()
        return
    
    print("[INFO] Bootstrapping PatternDB with default patterns...")
    
    accounts = ["instagram_personal", "instagram_brand", "facebook", "linkedin"]
    count = 0
    
    for account in accounts:
        for pattern in DEFAULT_PATTERNS:
            p = PatternDB(
                account=account,
                pattern_name=pattern["pattern_name"],
                trigger_conditions=pattern["trigger_conditions"],
                success_metric=pattern["success_metric"],
                avg_normalized_score=pattern["success_metric"],
                post_count=0,
                last_updated=datetime.utcnow()
            )
            db.add(p)
            count += 1
    
    db.commit()
    db.close()
    print(f"[PASS] PatternDB bootstrapped with {count} patterns across {len(accounts)} accounts.")

if __name__ == "__main__":
    main()
