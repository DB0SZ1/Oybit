"""
Oybit — Cultural Calendar (Agent A)
Determines if a day is sensitive or requires modified posting strategy due to cultural/religious events in Nigeria.
(GAPS_FINAL 4.4)
"""
from datetime import datetime, date
from config import EXAM_PERIOD_START, EXAM_PERIOD_END
from logger import get_logger

logger = get_logger("cultural_calendar")

# Hardcoded major holidays + manual Ramadan/Sallah overrides (typically managed via DB in full prod)
NIGERIA_HOLIDAYS_2024_2025 = {
    date(2024, 10, 1): "Independence Day",
    date(2024, 12, 25): "Christmas",
    date(2024, 12, 26): "Boxing Day",
    date(2025, 1, 1): "New Year's Day",
    date(2025, 3, 1): "Ramadan Starts", # Approx
    date(2025, 3, 30): "Eid al-Fitr", # Approx
    date(2025, 6, 6): "Eid al-Adha", # Approx
    date(2025, 10, 1): "Independence Day",
    date(2025, 12, 25): "Christmas",
    date(2025, 12, 26): "Boxing Day",
}

def is_sensitive_posting_day(check_date: date) -> dict:
    """Returns sensitivity info for a given date."""
    info = {
        "is_holiday": False,
        "holiday_name": None,
        "is_exam_period": False,
        "action": "normal"
    }

    if check_date in NIGERIA_HOLIDAYS_2024_2025:
        info["is_holiday"] = True
        info["holiday_name"] = NIGERIA_HOLIDAYS_2024_2025[check_date]
        info["action"] = "tone_down" # Tone down hyper-technical content, allow lifestyle
        logger.info(f"Cultural calendar detected holiday: {info['holiday_name']}")

    # Check exam period if configured
    if EXAM_PERIOD_START and EXAM_PERIOD_END:
        try:
            start = datetime.strptime(EXAM_PERIOD_START, "%Y-%m-%d").date()
            end = datetime.strptime(EXAM_PERIOD_END, "%Y-%m-%d").date()
            if start <= check_date <= end:
                info["is_exam_period"] = True
                info["action"] = "shift_to_tips" # Focus on academic/career tips
                logger.info("Cultural calendar detected exam period.")
        except ValueError:
            logger.error("Invalid exam period format in config. Expected YYYY-MM-DD.")

    return info

def apply_cultural_calendar_to_schedule(jobs: list, current_date: date = None) -> list:
    """
    Given a list of candidate posts/jobs, filters or modifies them based on the calendar.
    For simplicity, if it's a holiday, we might drop certain 'hard-selling' posts.
    """
    if current_date is None:
        current_date = datetime.utcnow().date()
        
    info = is_sensitive_posting_day(current_date)
    
    if info["action"] == "normal":
        return jobs
        
    filtered_jobs = []
    for job in jobs:
        # If it's a holiday, we might pause highly technical posts
        if info["is_holiday"] and job.get("format") == "deep_dive":
            logger.info(f"Delaying deep_dive post due to {info['holiday_name']}")
            continue
            
        # If exam period, we want to prioritize motivational or study tips
        if info["is_exam_period"] and job.get("topic_pillar") == "lifestyle":
            logger.info("Delaying purely lifestyle post during exam period")
            continue
            
        filtered_jobs.append(job)
        
    return filtered_jobs
