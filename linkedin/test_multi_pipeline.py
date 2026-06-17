import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), '..', 'hf_deploy'))

from backend.db.session import SessionLocal
from backend.api.pipeline import run_full_pipeline
from backend.db.models import Post

def test_pipeline():
    print("Testing Pipeline for multiple platforms...")
    db = SessionLocal()
    
    topic = "The hidden complexity behind simple UI buttons"
    platforms = ["twitter", "reddit", "linkedin"]
    
    for platform in platforms:
        print(f"\n--- Running pipeline for {platform} ---")
        try:
            result = run_full_pipeline(
                db=db,
                topic_brief=topic,
                platform=platform,
                account=platform,
                format_type="text",
                dry_run=True, # Dry run for content generation
                auto_schedule=True
            )
            print(f"Final Status: {result.get('final_status')}")
            for step in result.get("steps", []):
                print(f"  - {step}")
                
            if result.get("posts"):
                print("Generated Preview:")
                print(result["posts"][0]["content_preview"])
        except Exception as e:
            print(f"Error for {platform}: {e}")

if __name__ == "__main__":
    test_pipeline()
