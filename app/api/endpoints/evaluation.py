from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.schemas.build import EvaluationWebhook
from app.core.security import verify_secret
from app.db import get_db
from app.models import Submission, EvaluationResult

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook", status_code=200)
def evaluation_webhook(payload: EvaluationWebhook):
    # Verify webhook secret
    if not verify_secret(payload.secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")

    # Use DB session context
    with get_db() as db:  # type: Session
        try:
            # Upsert submission by (email, task, round, nonce)
            submission = (
                db.query(Submission)
                .filter(
                    Submission.email == payload.email,
                    Submission.task == payload.task,
                    Submission.round == payload.round,
                    Submission.nonce == payload.nonce,
                )
                .first()
            )
            if not submission:
                submission = Submission(
                    email=payload.email,
                    task=payload.task,
                    round=payload.round,
                    nonce=payload.nonce,
                    repo_url=payload.repo_url,
                    pages_url=payload.pages_url,
                    commit_sha=payload.commit_sha,
                )
                db.add(submission)
                db.flush()  # get ID
            else:
                # update URLs/commit if changed
                submission.repo_url = payload.repo_url
                submission.pages_url = payload.pages_url
                submission.commit_sha = payload.commit_sha

            # Create evaluation result row
            result = EvaluationResult(
                submission_id=submission.id,
                status=payload.status,
                score=payload.score,
                feedback=payload.feedback,
                passed=payload.passed,
            )
            db.add(result)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"DB error persisting evaluation: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    return {"ok": True}
