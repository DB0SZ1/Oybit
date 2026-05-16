import os
from dotenv import load_dotenv

# Load from backend/.env explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from backend.db.session import SessionLocal
from backend.api.pipeline import run_full_pipeline

def trigger_carousel():
    db = SessionLocal()
    try:
        print("Triggering 6-slide carousel generation...")
        result = run_full_pipeline(
            db=db,
            topic_brief="Write a highly engaging 6-slide carousel about why 'Done is better than perfect' for software engineers. It MUST contain exactly 6 distinct slides.",
            platform="instagram",
            account="instagram_personal",
            format_type="carousel",
            auto_schedule=False
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    trigger_carousel()
