"""
Follow Worker — Scheduled daily worker that executes follow/unfollow strategy.
Runs at FOLLOW_WORKER_HOUR (default 10AM WAT) if FOLLOW_STRATEGY_ENABLED=true.
"""

import os
import sys
import time
import schedule
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import get_logger
from db.session import get_session

logger = get_logger("workers.follow_worker")

FOLLOW_STRATEGY_ENABLED = os.getenv("FOLLOW_STRATEGY_ENABLED", "false").lower() == "true"
FOLLOW_WORKER_HOUR = os.getenv("FOLLOW_WORKER_HOUR", "10:00")
SEED_ACCOUNTS = os.getenv("FOLLOW_SEED_ACCOUNTS", "").split(",")  # comma-separated seed account IDs


def run_follow_cycle():
    """Execute one follow/unfollow cycle."""
    if not FOLLOW_STRATEGY_ENABLED:
        logger.info("Follow strategy disabled — skipping cycle")
        return

    logger.info("Follow worker cycle starting")
    db = get_session()

    try:
        from growth.follow_strategy import FollowManager
        from db.models import WorkerHeartbeat

        manager = FollowManager()

        # 1. Execute unfollows first (free up capacity)
        for account in ["instagram_personal", "instagram_brand"]:
            try:
                unfollowed = manager.execute_unfollows(account)
                logger.info("Unfollows executed", extra={
                    "account": account,
                    "unfollowed": unfollowed,
                })
            except Exception as e:
                logger.error("Unfollow cycle failed", extra={
                    "account": account,
                    "error": str(e),
                })

        # 2. Find and execute new follows
        for seed_id in SEED_ACCOUNTS:
            seed_id = seed_id.strip()
            if not seed_id:
                continue

            try:
                targets = manager.find_follow_targets(seed_id)
                if targets:
                    for account in ["instagram_personal"]:
                        followed = manager.execute_follows(targets[:20], account)
                        logger.info("Follows executed", extra={
                            "seed": seed_id,
                            "account": account,
                            "targets_found": len(targets),
                            "followed": followed,
                        })
            except Exception as e:
                logger.error("Follow cycle failed", extra={
                    "seed": seed_id,
                    "error": str(e),
                })

        # 3. Update heartbeat
        try:
            heartbeat = db.query(WorkerHeartbeat).filter_by(
                worker_name="follow_worker"
            ).first()
            if heartbeat:
                heartbeat.last_heartbeat = datetime.utcnow()
                heartbeat.last_run = datetime.utcnow()
                heartbeat.last_status = "ok"
            else:
                db.add(WorkerHeartbeat(
                    worker_name="follow_worker",
                    last_heartbeat=datetime.utcnow(),
                    last_run=datetime.utcnow(),
                    last_status="ok",
                ))
            db.commit()
        except Exception as e:
            logger.error("Heartbeat update failed", extra={"error": str(e)})

    except Exception as e:
        logger.error("Follow worker cycle failed", extra={"error": str(e)})
    finally:
        db.close()

    logger.info("Follow worker cycle complete")


def main():
    """Entry point for follow worker."""
    logger.info("Follow worker starting", extra={
        "enabled": FOLLOW_STRATEGY_ENABLED,
        "hour": FOLLOW_WORKER_HOUR,
        "seed_accounts": len([s for s in SEED_ACCOUNTS if s.strip()]),
    })

    if not FOLLOW_STRATEGY_ENABLED:
        logger.info("Follow strategy disabled. Set FOLLOW_STRATEGY_ENABLED=true to enable.")
        # Still run the loop but skip — allows restarting without redeploy
        pass

    schedule.every().day.at(FOLLOW_WORKER_HOUR).do(run_follow_cycle)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
