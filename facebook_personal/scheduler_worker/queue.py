"""
Oybit — Scheduler Queue
SQLAlchemy-based job queue for scheduling post dispatch.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc

from db.session import get_db, SessionLocal
from db.models import SchedulerJob

logger = logging.getLogger(__name__)

class SchedulerQueue:
    """SQLAlchemy job queue for scheduling posts."""

    def __init__(self, db_session: Session = None):
        self.session_provided = db_session is not None
        self.db = db_session

    def _get_db(self) -> Session:
        if self.session_provided:
            return self.db
        return SessionLocal()

    def _close_db(self, db: Session):
        if not self.session_provided:
            db.close()

    def add_job(self, post_id: int, account: str, scheduled_at: datetime) -> int:
        """Add a new job to the queue. Returns job ID."""
        db = self._get_db()
        try:
            job = SchedulerJob(
                post_id=post_id,
                account=account,
                scheduled_at=scheduled_at,
                status="pending",
                attempts=0,
                created_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            logger.info(f"Added job {job.id}: post {post_id} → {account} at {scheduled_at}")
            return job.id
        finally:
            self._close_db(db)

    def get_due_jobs(self) -> list[dict]:
        """
        Get all jobs that are due for dispatch.
        Conditions: scheduled_at <= now, status = pending, attempts < 3
        """
        db = self._get_db()
        try:
            now = datetime.utcnow()
            jobs = db.query(SchedulerJob).filter(
                SchedulerJob.scheduled_at <= now,
                SchedulerJob.status == "pending",
                SchedulerJob.attempts < 3
            ).order_by(asc(SchedulerJob.scheduled_at)).with_for_update().all()
            
            # We return dicts to keep compatibility with old queue API
            return [{"id": j.id, "post_id": j.post_id, "account": j.account, "attempts": j.attempts} for j in jobs]
        finally:
            # We don't commit here because with_for_update keeps the lock until commit/rollback
            # The caller handles the transaction or we just release it if not provided
            if not self.session_provided:
                db.rollback()
                db.close()

    def mark_running(self, job_id: int):
        """Mark a job as currently running."""
        db = self._get_db()
        try:
            job = db.query(SchedulerJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()
        finally:
            self._close_db(db)

    def mark_done(self, job_id: int):
        """Mark a job as completed."""
        db = self._get_db()
        try:
            job = db.query(SchedulerJob).filter_by(id=job_id).first()
            if job:
                job.status = "done"
                db.commit()
        finally:
            self._close_db(db)

    def mark_failed(self, job_id: int, error: str = None):
        """Mark a job as failed with optional error message."""
        db = self._get_db()
        try:
            job = db.query(SchedulerJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.last_error = error
                db.commit()
        finally:
            self._close_db(db)

    def increment_attempts(self, job_id: int):
        """Increment the attempt counter for a job."""
        db = self._get_db()
        try:
            job = db.query(SchedulerJob).filter_by(id=job_id).first()
            if job:
                job.attempts += 1
                db.commit()
        finally:
            self._close_db(db)

    def reschedule(self, job_id: int, new_time: datetime):
        """Reschedule a job by setting new scheduled_at and status back to pending."""
        db = self._get_db()
        try:
            job = db.query(SchedulerJob).filter_by(id=job_id).first()
            if job:
                job.status = "pending"
                job.scheduled_at = new_time
                db.commit()
        finally:
            self._close_db(db)
