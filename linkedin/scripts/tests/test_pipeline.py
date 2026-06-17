import sys
import os

# Add the root 'linkedin' directory to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db.session import SessionLocal
from api_routes.content import simulate_pipeline
from db.models import Post, AuditLog
import logging

logging.basicConfig(level=logging.INFO)

def run_test():
    db = SessionLocal()
    print("Testing Pipeline Execution...")
    simulate_pipeline(db)
    
    print("Fetching the latest post...")
    latest_post = db.query(Post).order_by(Post.created_at.desc()).first()
    if latest_post:
        print(f"Status: {latest_post.status}")
        print(f"Text snippet: {latest_post.content_text[:100]}...")
        
    print("Fetching the latest audit logs...")
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(5).all()
    for log in reversed(logs):
        print(f"[{log.action}] - {log.details}")

if __name__ == "__main__":
    run_test()
