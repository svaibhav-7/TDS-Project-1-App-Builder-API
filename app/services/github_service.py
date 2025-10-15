import os
import base64
from github import Github, GithubException
from github.ContentFile import ContentFile
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime

from app.config import settings
from github import InputGitTreeElement
import httpx

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.github = Github(settings.GITHUB_TOKEN)
        self.user = self.github.get_user()
    
    def create_repository(self, name: str, description: str = "", private: bool = False):
        """Create a new GitHub repository."""
        try:
            if settings.GITHUB_ORG:
                org = self.github.get_organization(settings.GITHUB_ORG)
                repo = org.create_repo(name, description=description, private=private)
            else:
                repo = self.user.create_repo(name, description=description, private=private)
            
            # Initialize with a README
            repo.create_file(
                "README.md",
                "Initial commit: Add README",
                f"# {name}\n\n{description}"
            )
            # Add MIT LICENSE
            mit_license = (
                "MIT License\n\n"
                "Copyright (c) "
                f"{datetime.utcnow().year} {repo.owner.login}\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
                "of this software and associated documentation files (the \"Software\"), to deal\n"
                "in the Software without restriction, including without limitation the rights\n"
                "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
                "copies of the Software, and to permit persons to whom the Software is\n"
                "furnished to do so, subject to the following conditions:\n\n"
                "The above copyright notice and this permission notice shall be included in all\n"
                "copies or substantial portions of the Software.\n\n"
                "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
                "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
                "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
                "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
                "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
                "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
                "SOFTWARE.\n"
            )
            try:
                repo.create_file("LICENSE", "Add MIT LICENSE", mit_license)
            except GithubException:
                pass
            
            return repo
        except GithubException as e:
            # If repo already exists, fetch and return it (idempotent behavior)
            msg = str(e).lower()
            if getattr(e, "status", None) == 422 and "name already exists" in msg:
                try:
                    if settings.GITHUB_ORG:
                        return self.github.get_repo(f"{settings.GITHUB_ORG}/{name}")
                    else:
                        return self.github.get_repo(f"{self.user.login}/{name}")
                except Exception:
                    pass
            logger.error(f"Failed to create repository: {e}")
            raise
    
    def enable_pages(self, repo_name: str, branch: str = "main"):
        """Enable GitHub Pages for the repository by setting source to gh-pages via REST API.
        Creates gh-pages from the specified branch if missing.
        """
        try:
            if settings.GITHUB_ORG:
                full_name = f"{settings.GITHUB_ORG}/{repo_name}"
                repo = self.github.get_repo(full_name)
            else:
                full_name = f"{self.user.login}/{repo_name}"
                repo = self.github.get_repo(full_name)

            # Ensure gh-pages branch exists (pointing at current branch commit)
            try:
                repo.get_branch("gh-pages")
            except GithubException:
                src_branch = repo.get_branch(branch)
                repo.create_git_ref(ref="refs/heads/gh-pages", sha=src_branch.commit.sha)

            # Configure Pages source via GitHub REST API
            api_url = f"https://api.github.com/repos/{full_name}/pages"
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"token {settings.GITHUB_TOKEN}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            payload = {"source": {"branch": "gh-pages", "path": "/"}}
            try:
                with httpx.Client(timeout=15.0) as client:
                    # PUT to set the source (idempotent)
                    resp = client.put(api_url, headers=headers, json=payload)
                    if resp.status_code not in (201, 204, 202):
                        logger.info(f"Pages config PUT returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.info(f"Pages configuration via REST failed: {e}")

            return f"https://{repo.owner.login}.github.io/{repo.name}/"
        except GithubException as e:
            logger.error(f"Failed to enable GitHub Pages: {e}")
            raise
    
    def commit_files(self, repo_name: str, files: Dict[str, str], commit_message: str, branch: str = "main"):
        """Commit multiple files to the repository."""
        try:
            if settings.GITHUB_ORG:
                repo = self.github.get_repo(f"{settings.GITHUB_ORG}/{repo_name}")
            else:
                repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            
            # Get the current commit to get the tree
            branch_obj = repo.get_branch(branch)
            base_tree = repo.get_git_tree(sha=branch_obj.commit.sha)
            
            # Create blobs and tree elements using InputGitTreeElement
            tree_elements = []
            for path, content in files.items():
                if isinstance(content, str):
                    text = content
                else:
                    text = content.decode('utf-8')
                blob = repo.create_git_blob(text, 'utf-8')
                element = InputGitTreeElement(path=path, mode="100644", type="blob", sha=blob.sha)
                tree_elements.append(element)
            
            # Create a new tree
            tree = repo.create_git_tree(tree_elements, base_tree)
            
            # Create a new commit
            parent = repo.get_git_commit(sha=branch_obj.commit.sha)
            commit = repo.create_git_commit(commit_message, tree, [parent])
            
            # Update the branch reference
            branch_ref = repo.get_git_ref(f"heads/{branch}")
            branch_ref.edit(sha=commit.sha)
            
            return commit.sha
        except GithubException as e:
            logger.error(f"Failed to commit files: {e}")
            raise
    
    def get_repository_urls(self, repo_name: str) -> Dict[str, str]:
        """Get repository URLs."""
        try:
            if settings.GITHUB_ORG:
                repo = self.github.get_repo(f"{settings.GITHUB_ORG}/{repo_name}")
            else:
                repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            
            return {
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "pages_url": f"https://{repo.owner.login}.github.io/{repo.name}/"
            }
        except GithubException as e:
            logger.error(f"Failed to get repository URLs: {e}")
            raise

# Create a singleton instance
github_service = GitHubService()
