import re
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevPilot-AI-App"
        }
        if self.token:
            # support both "token x" and token direct
            if not self.token.lower().startswith("token ") and not self.token.lower().startswith("bearer "):
                self.headers["Authorization"] = f"token {self.token}"
            else:
                self.headers["Authorization"] = self.token

    @staticmethod
    def parse_url(url: str) -> Tuple[str, str]:
        """
        Parses a GitHub URL into (owner, repo).
        Supports:
        - https://github.com/owner/repo
        - github.com/owner/repo
        - owner/repo
        """
        # Clean URL
        cleaned = url.strip()
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]
        
        # Regex matching
        pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)"
        match = re.match(pattern, cleaned, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
        
        # Fallback to direct owner/repo format
        parts = [p for p in cleaned.split("/") if p]
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        
        raise ValueError("Invalid GitHub Repository URL or path")

    async def get_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch general repository metadata."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise ValueError(f"Repository '{owner}/{repo}' not found or is private")
            response.raise_for_status()
            return response.json()

    async def get_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository language breakdown."""
        url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            return {}

    async def get_commits(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch the list of recent commits."""
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={limit}"
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            return []

    async def get_file_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch the recursive file tree for the repository default branch."""
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                tree_data = response.json()
                return tree_data.get("tree", [])
            
            # Fallback if branch is master or something else
            if branch == "main":
                # Try fallback to master
                url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = await client.get(url)
                if response.status_code == 200:
                    tree_data = response.json()
                    return tree_data.get("tree", [])
            return []

    async def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> Optional[str]:
        """Fetch content of a specific file from the repository."""
        # Using raw.githubusercontent.com to avoid base64 decoding issues or REST overhead
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            
            # Try master fallback
            if branch == "main":
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
            return None

    async def fetch_multiple_files(self, owner: str, repo: str, paths: List[str], branch: str = "main") -> Dict[str, Optional[str]]:
        """Fetch multiple files concurrently using asyncio."""
        tasks = [self.get_file_content(owner, repo, path, branch) for path in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        file_contents = {}
        for path, result in zip(paths, results):
            if isinstance(result, Exception) or result is None:
                file_contents[path] = None
            else:
                file_contents[path] = result
        return file_contents
