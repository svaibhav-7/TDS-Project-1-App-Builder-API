from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    task = Column(String, index=True, nullable=False)
    round = Column(Integer, nullable=False)
    nonce = Column(String, index=True, nullable=False)
    repo_url = Column(String, nullable=False)
    pages_url = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    evaluations = relationship("EvaluationResult", back_populates="submission", cascade="all, delete-orphan")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submission = relationship("Submission", back_populates="evaluations")
