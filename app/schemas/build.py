from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Attachment(BaseModel):
    """Represents a file attachment in a build request."""
    name: str = Field(..., description="Name of the attachment file")
    url: str = Field(..., description="URL or data URI of the attachment")
    content_type: Optional[str] = Field(None, description="MIME type of the attachment")

class BuildRequest(BaseModel):
    """Request model for building or updating an application."""
    email: str = Field(..., description="Email of the user making the request")
    secret: str = Field(..., description="Secret key for authentication")
    task: str = Field(..., description="Unique identifier for the task")
    round: int = Field(1, description="Round number for the task")
    nonce: str = Field(..., description="Unique nonce for the request")
    brief: str = Field(..., description="Description of what the app should do")
    checks: List[str] = Field(default_factory=list, description="List of requirements/checks")
    evaluation_url: str = Field(..., description="URL to notify when build is complete")
    attachments: Optional[List[Attachment]] = Field(
        None, 
        description="Optional file attachments for the build"
    )

class BuildResponse(BaseModel):
    """Response model for build and update operations."""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Human-readable message about the operation")
    repo_url: str = Field(..., description="URL of the GitHub repository")
    pages_url: str = Field(..., description="URL of the deployed GitHub Pages site")
    commit_sha: Optional[str] = Field(None, description="SHA of the latest commit")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the response"
    )

class EvaluationRequest(BaseModel):
    """Request model for evaluating an application."""
    email: str = Field(..., description="Email of the user")
    task: str = Field(..., description="Task identifier")
    round: int = Field(..., description="Round number")
    nonce: str = Field(..., description="Nonce from the original request")
    repo_url: str = Field(..., description="URL of the GitHub repository")
    commit_sha: str = Field(..., description="SHA of the commit being evaluated")
    pages_url: str = Field(..., description="URL of the deployed application")

class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    status: str = Field(..., description="Status of the evaluation")
    score: Optional[float] = Field(None, description="Numeric score (0-100)")
    feedback: Optional[Dict[str, Any]] = Field(
        None, 
        description="Detailed feedback and results"
    )
    passed: bool = Field(..., description="Whether the evaluation passed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the evaluation"
    )

class EvaluationWebhook(BaseModel):
    """Webhook payload model for evaluation results."""
    email: str = Field(..., description="Email of the user")
    task: str = Field(..., description="Task identifier")
    round: int = Field(..., description="Round number")
    nonce: str = Field(..., description="Nonce from the original request")
    repo_url: str = Field(..., description="URL of the GitHub repository")
    commit_sha: str = Field(..., description="SHA of the commit being evaluated")
    pages_url: str = Field(..., description="URL of the deployed application")
    secret: str = Field(..., description="Webhook secret for verification")
    status: str = Field(..., description="Status of the evaluation")
    score: Optional[float] = Field(None, description="Numeric score (0-100)")
    feedback: Optional[Dict[str, Any]] = Field(None, description="Detailed feedback and results")
    passed: bool = Field(..., description="Whether the evaluation passed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the evaluation")

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current server time"
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of service dependencies"
    )
