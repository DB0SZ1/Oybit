import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), '..', 'hf_deploy'))

from backend.publishers.twilio_notifier import send_twilio_notification

def test_twilio():
    print("Testing Twilio Notifier...")
    # Using real SMS, not dry_run
    result = send_twilio_notification(
        post_id="TEST-123",
        account="twitter",
        content_text="This is a test tweet from your automated system! [SCREENSHOT: A cool graphic about AI]",
        dry_run=False
    )
    print(f"Result: {result}")

if __name__ == "__main__":
    test_twilio()
