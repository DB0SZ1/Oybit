"""
Onboarding Calibration — Agent A Module

After every manual post Ahmad publishes directly:
- Prompts "How authentically does this sound like you? (1-10, why?)"
- Stores rating + reasoning
- Low ratings (<6) trigger targeted follow-up questions
- High ratings (≥8) reinforce current persona weights
- All responses appended to simulation_log.md
"""

import os
from datetime import datetime
from backend.logger import get_logger

logger = get_logger("onboarding.calibration")

PERSONA_DIR = os.getenv("PERSONA_DIR", "/data/personas/ahmad")
SIMULATION_LOG_PATH = os.path.join(PERSONA_DIR, "simulation_log.md")


def submit_calibration_rating(
    post_text: str,
    rating: int,
    reasoning: str,
    platform: str,
    db_session=None,
) -> dict:
    """
    Process Ahmad's authenticity rating of a generated post.

    Args:
        post_text: the post text that was reviewed
        rating: 1-10 authenticity score
        reasoning: Ahmad's explanation of the rating
        platform: which platform the post was for
        db_session: optional DB session for persisting

    Returns:
        dict with processing result and any follow-up actions
    """
    if not 1 <= rating <= 10:
        return {"error": "Rating must be between 1 and 10"}

    # 1. Append to simulation_log.md (NEVER overwrite, only append)
    _append_to_simulation_log(post_text, rating, reasoning, platform)

    # 2. Store in DB if session provided
    if db_session:
        _store_calibration_in_db(db_session, post_text, rating, reasoning, platform)

    # 3. Determine follow-up action based on rating
    follow_up = None
    if rating < 6:
        follow_up = _generate_low_rating_followup(rating, reasoning)
        logger.warning("Low authenticity rating", extra={
            "rating": rating,
            "platform": platform,
            "reasoning_preview": reasoning[:100],
        })
    elif rating >= 8:
        _reinforce_persona_weights(platform, reasoning)
        logger.info("High authenticity rating — reinforcing persona", extra={
            "rating": rating,
            "platform": platform,
        })

    result = {
        "rating": rating,
        "stored": True,
        "follow_up_questions": follow_up,
        "action": "reinforce" if rating >= 8 else "investigate" if rating < 6 else "noted",
    }

    logger.info("Calibration rating submitted", extra=result)
    return result


def _append_to_simulation_log(post_text: str, rating: int, reasoning: str, platform: str):
    """Append calibration entry to simulation_log.md (append-only, never truncate)."""
    entry = f"""
## Calibration — {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

Platform: {platform}
Post text: {post_text[:200]}{'...' if len(post_text) > 200 else ''}
Authenticity rating: {rating}/10
Reasoning: {reasoning}
What AI learned: {"Voice match is strong — current persona weights are accurate" if rating >= 8 else f"Voice mismatch detected — Ahmad says: {reasoning[:100]}"}
"""
    try:
        os.makedirs(os.path.dirname(SIMULATION_LOG_PATH), exist_ok=True)
        with open(SIMULATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        logger.info("Calibration appended to simulation_log.md")
    except Exception as e:
        logger.error("Failed to append to simulation_log.md", extra={"error": str(e)})


def _store_calibration_in_db(db_session, post_text, rating, reasoning, platform):
    """Store calibration as SimulationLogEntry in DB."""
    try:
        from backend.db.models import SimulationLogEntry
        entry = SimulationLogEntry(
            session_date=datetime.utcnow().strftime("%Y-%m-%d"),
            sim_number=0,  # 0 = calibration, not simulation
            platform=platform,
            scenario_type="calibration",
            shown_content=post_text[:500],
            user_reaction=f"{rating}/10",
            user_decision=reasoning[:500],
            ai_learned=(
                "Voice match confirmed — persona weights accurate"
                if rating >= 8
                else f"Voice drift indicator — {reasoning[:200]}"
            ),
        )
        db_session.add(entry)
        db_session.commit()
    except Exception as e:
        logger.error("DB calibration write failed", extra={"error": str(e)})
        db_session.rollback()


LOW_RATING_FOLLOWUP_QUESTIONS = {
    "tone": [
        "What specifically sounds off about the tone? Too formal? Too casual? Too aggressive?",
        "If you were saying this out loud, what words would you change?",
        "Can you rewrite just the first sentence the way you'd actually say it?",
    ],
    "content": [
        "Is the topic wrong, or is the angle wrong?",
        "What's the real insight you'd want to share about this?",
        "Would you ever post this exact idea? If yes, how would you frame it differently?",
    ],
    "style": [
        "Is this too long or too short for how you'd normally write?",
        "Do you use emojis like this? More? Less? Different ones?",
        "Is the CTA (call to action) right? Would you phrase it differently?",
    ],
}


def _generate_low_rating_followup(rating: int, reasoning: str) -> list:
    """
    Generate targeted follow-up questions based on low rating.
    Uses keyword detection on the reasoning to pick relevant questions.
    """
    reasoning_lower = reasoning.lower()

    questions = []

    if any(kw in reasoning_lower for kw in ["tone", "formal", "casual", "sound", "voice", "stiff"]):
        questions.extend(LOW_RATING_FOLLOWUP_QUESTIONS["tone"][:2])
    elif any(kw in reasoning_lower for kw in ["topic", "angle", "wrong", "wouldn't say", "wouldn't post"]):
        questions.extend(LOW_RATING_FOLLOWUP_QUESTIONS["content"][:2])
    elif any(kw in reasoning_lower for kw in ["long", "short", "emoji", "style", "format"]):
        questions.extend(LOW_RATING_FOLLOWUP_QUESTIONS["style"][:2])
    else:
        # General follow-up for unclassified low ratings
        questions = [
            LOW_RATING_FOLLOWUP_QUESTIONS["tone"][0],
            LOW_RATING_FOLLOWUP_QUESTIONS["content"][0],
        ]

    if rating <= 3:
        questions.append("Can you rewrite this entire post how you'd actually write it?")

    return questions


def _reinforce_persona_weights(platform: str, reasoning: str):
    """
    When rating is high (≥8), reinforce current persona weights.
    Log the positive signal for the updater to consider.
    """
    logger.info("Reinforcing persona weights", extra={
        "platform": platform,
        "positive_signal": reasoning[:200],
    })
    # The actual weight reinforcement happens via the learning engine's
    # pattern analysis — high-rated posts contribute to winning patterns


def get_calibration_history(db_session, limit: int = 20) -> list:
    """Get recent calibration entries."""
    try:
        from backend.db.models import SimulationLogEntry
        entries = db_session.query(SimulationLogEntry).filter_by(
            scenario_type="calibration"
        ).order_by(SimulationLogEntry.appended_at.desc()).limit(limit).all()

        return [
            {
                "date": e.session_date,
                "platform": e.platform,
                "rating": e.user_reaction,
                "reasoning": e.user_decision,
                "ai_learned": e.ai_learned,
            }
            for e in entries
        ]
    except Exception as e:
        logger.error("Failed to fetch calibration history", extra={"error": str(e)})
        return []
