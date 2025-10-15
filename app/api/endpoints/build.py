from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import re
import asyncio
import httpx

from app.schemas.build import BuildRequest, BuildResponse
from app.services.github_service import github_service
from app.services.llm_service import llm_service
from app.services.evaluation_client import evaluation_client
from app.core.security import verify_secret
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=BuildResponse)
async def build_app(request: BuildRequest):
    """
    Build and deploy a new application based on the provided specifications.
    
    This endpoint handles the entire process of creating a new application:
    1. Validates the request and authenticates the user
    2. Generates the application code using an LLM
    3. Creates a new GitHub repository
    4. Commits the generated code
    5. Enables GitHub Pages
    6. Returns the deployment details
    """
    # Verify the secret
    if not verify_secret(request.secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret"
        )
    
    try:
        logger.info(f"Starting build for task: {request.task}")
        
        # Use a stable, task-based repository name so round 2 can locate it
        safe_task = re.sub(r"[^a-zA-Z0-9-_]", "-", request.task.strip()).lower()
        repo_name = f"{safe_task}"
        
        # Generate app structure using LLM
        requirements = {
            "brief": request.brief,
            "checks": request.checks,
            "attachments": request.attachments or []
        }
        
        logger.info("Generating app structure...")
        app_files = await llm_service.generate_app_structure(requirements)
        
        # Add a timestamp to the README
        if "README.md" in app_files:
            app_files["README.md"] += f"\n\n---\n*Generated on {datetime.utcnow().isoformat()}*"
        
        # Create GitHub repository
        logger.info(f"Creating repository: {repo_name}")
        repo = github_service.create_repository(
            name=repo_name,
            description=f"Generated app for task: {request.task}",
            private=False
        )
        
        # Commit files to the repository
        logger.info("Committing files...")
        commit_sha = github_service.commit_files(
            repo_name=repo.name,
            files=app_files,
            commit_message="Initial commit: Generated app structure"
        )
        
        # Enable GitHub Pages
        logger.info("Enabling GitHub Pages...")
        pages_url = github_service.enable_pages(repo_name=repo.name)
        
        # Get repository URLs
        repo_urls = github_service.get_repository_urls(repo_name=repo.name)

        # Verify GitHub Pages availability with retries
        async with httpx.AsyncClient(timeout=10.0) as client:
            ok = False
            delay = 1
            for _ in range(7):  # up to ~2 minutes total
                try:
                    resp = await client.get(pages_url, headers={"Cache-Control": "no-cache"})
                    if resp.status_code == 200:
                        ok = True
                        break
                    logger.info(f"Pages not ready ({resp.status_code}). Retrying in {delay}s...")
                except Exception as e:
                    logger.info(f"Pages check error: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)
            if not ok:
                logger.warning("GitHub Pages did not return 200 within retry window")
        
        logger.info(f"Build completed successfully for {repo_name}")
        
        
        # Notify evaluation endpoint (await with retries)
        try:
            await evaluation_client.notify(
                url=request.evaluation_url,
                payload={
                    "email": request.email,
                    "task": request.task,
                    "round": request.round,
                    "nonce": request.nonce,
                    "repo_url": repo_urls["html_url"],
                    "commit_sha": commit_sha,
                    "pages_url": pages_url,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to notify evaluation URL: {e}")

        return BuildResponse(
            status="success",
            message="Application built and deployed successfully",
            repo_url=repo_urls["html_url"],
            pages_url=pages_url,
            commit_sha=commit_sha
        )
        
    except Exception as e:
        logger.error(f"Error building application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build application: {str(e)}"
        )

@router.post("/update", response_model=BuildResponse)
async def update_app(request: BuildRequest):
    """
    Update an existing application based on new requirements.
    
    This endpoint handles updating an existing application:
    1. Validates the request and authenticates the user
    2. Fetches the existing repository
    3. Generates updated code using an LLM
    4. Creates a new commit with the changes
    5. Updates GitHub Pages if necessary
    6. Returns the update details
    """
    # Verify the secret
    if not verify_secret(request.secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret"
        )
    
    try:
        logger.info(f"Starting update for task: {request.task}, round: {request.round}")
        
        # Use the same stable, task-based repository name as in build phase
        safe_task = re.sub(r"[^a-zA-Z0-9-_]", "-", request.task.strip()).lower()
        repo_name = f"{safe_task}"
        
        # Get the existing repository
        if settings.GITHUB_ORG:
            repo = github_service.github.get_repo(f"{settings.GITHUB_ORG}/{repo_name}")
        else:
            repo = github_service.github.get_repo(f"{github_service.user.login}/{repo_name}")
        
        # Get the current files in the repository
        contents = repo.get_contents("")
        existing_files = {}
        
        # Process repository contents (this is a simplified version)
        for content_file in contents:
            if content_file.type == "file":
                existing_files[content_file.path] = content_file.decoded_content.decode('utf-8')
        
        # Generate updated files using LLM
        requirements = {
            "brief": request.brief,
            "checks": request.checks,
            "attachments": request.attachments or [],
            "existing_files": existing_files,
            "update_instructions": f"Update the application based on round {request.round} requirements"
        }
        
        logger.info("Generating updated files...")
        updated_files = await llm_service.generate_app_structure(requirements)
        
        # Commit the updated files
        logger.info("Committing updates...")
        commit_sha = github_service.commit_files(
            repo_name=repo_name,
            files=updated_files,
            commit_message=f"Update: Round {request.round} - {request.brief[:50]}..."
        )
        
        # Ensure GitHub Pages URL and verify availability
        repo_urls = github_service.get_repository_urls(repo_name=repo_name)
        pages_url = repo_urls.get("pages_url")
        if pages_url:
            async with httpx.AsyncClient(timeout=10.0) as client:
                ok = False
                delay = 1
                for _ in range(7):
                    try:
                        resp = await client.get(pages_url, headers={"Cache-Control": "no-cache"})
                        if resp.status_code == 200:
                            ok = True
                            break
                        logger.info(f"Pages not ready after update ({resp.status_code}). Retrying in {delay}s...")
                    except Exception as e:
                        logger.info(f"Pages check error after update: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 30)
                if not ok:
                    logger.warning("GitHub Pages did not return 200 within retry window after update")

        # Notify evaluation endpoint
        try:
            await evaluation_client.notify(
                url=request.evaluation_url,
                payload={
                    "email": request.email,
                    "task": request.task,
                    "round": request.round,
                    "nonce": request.nonce,
                    "repo_url": repo_urls["html_url"],
                    "commit_sha": commit_sha,
                    "pages_url": pages_url or repo_urls.get("pages_url"),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to notify evaluation URL after update: {e}")

        logger.info(f"Update completed successfully for {repo_name}")
        
        return BuildResponse(
            status="success",
            message=f"Application updated successfully for round {request.round}",
            repo_url=repo_urls["html_url"],
            pages_url=pages_url or repo_urls.get("pages_url"),
            commit_sha=commit_sha
        )
        
    except Exception as e:
        logger.error(f"Error updating application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )
