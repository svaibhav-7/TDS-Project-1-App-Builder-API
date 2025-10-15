from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Submission, EvaluationResult

router = APIRouter()

@router.get("/submissions")
def list_submissions(
    email: Optional[str] = None,
    task: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_db() as db:  # type: Session
        q = db.query(Submission)
        if email:
            q = q.filter(Submission.email == email)
        if task:
            q = q.filter(Submission.task == task)
        total = q.count()
        rows = (
            q.order_by(Submission.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "total": total,
            "items": [
                {
                    "id": s.id,
                    "email": s.email,
                    "task": s.task,
                    "round": s.round,
                    "nonce": s.nonce,
                    "repo_url": s.repo_url,
                    "pages_url": s.pages_url,
                    "commit_sha": s.commit_sha,
                    "created_at": s.created_at.isoformat(),
                }
                for s in rows
            ],
        }

@router.get("/evaluations")
def list_evaluations(
    email: Optional[str] = None,
    task: Optional[str] = None,
    round: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_db() as db:  # type: Session
        # Join to pull email/task/round
        from sqlalchemy import select
        from sqlalchemy.orm import aliased

        q = db.query(EvaluationResult, Submission).join(Submission, EvaluationResult.submission_id == Submission.id)
        if email:
            q = q.filter(Submission.email == email)
        if task:
            q = q.filter(Submission.task == task)
        if round is not None:
            q = q.filter(Submission.round == round)
        total = q.count()
        rows = (
            q.order_by(EvaluationResult.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "total": total,
            "items": [
                {
                    "id": ev.id,
                    "email": sub.email,
                    "task": sub.task,
                    "round": sub.round,
                    "status": ev.status,
                    "score": ev.score,
                    "passed": ev.passed,
                    "feedback": ev.feedback,
                    "created_at": ev.created_at.isoformat(),
                }
                for ev, sub in rows
            ],
        }
