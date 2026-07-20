import asyncio
import json
import logging
from typing import Any, Dict, List

from app.config import settings

logger = logging.getLogger(__name__)


class InsightGenerator:
    @classmethod
    def build_candidates(cls, analysis: Dict[str, Any], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        documentation = analysis.get("documentation", {})
        structure = analysis.get("structure", {})
        security = analysis.get("security", {})
        commits = analysis.get("commits", {})

        if not documentation.get("readme_exists"):
            candidates.append({"type": "warning", "message": "No README was found; add setup and usage guidance for contributors.", "file": "README.md"})
        for deduction in documentation.get("deductions", []) + structure.get("deductions", []) + commits.get("deductions", []):
            candidates.append({"type": "warning", "message": deduction["explanation"], "file": deduction.get("file_involved")})
        for secret in security.get("secrets", []):
            candidates.append({"type": "warning", "message": f"Potential {secret['secret_type']} exposure detected; rotate it and remove it from source control.", "file": secret.get("file_path")})
        for vulnerability in security.get("vulnerabilities", []):
            candidates.append({"type": "warning", "message": f"{vulnerability['package_name']} has a {vulnerability['severity']} OSV vulnerability: {vulnerability['description']}", "file": vulnerability.get("file_path")})
        if structure.get("has_tests"):
            candidates.append({"type": "good", "message": "Automated tests were detected in the repository.", "file": None})
        if structure.get("has_github_actions"):
            candidates.append({"type": "good", "message": "A GitHub Actions workflow is present for automated checks.", "file": ".github/workflows"})
        for file_data in snapshot.get("file_tree", []):
            if isinstance(file_data, dict) and file_data.get("size", 0) > 50000:
                candidates.append({"type": "info", "message": f"This file is large ({file_data['size']:,} bytes); consider splitting it if it contains multiple responsibilities.", "file": file_data.get("path")})
        return candidates[:12]

    @classmethod
    async def generate(cls, analysis: Dict[str, Any], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = cls.build_candidates(analysis, snapshot)
        if not candidates or not settings.GEMINI_API_KEY:
            return candidates
        prompt = f"""Turn the following repository findings into at most 10 concise, specific insights. Return only a JSON array with objects using exactly: type (warning, info, or good), message, file (string or null). Do not invent facts or paths.\n\nFindings:\n{json.dumps(candidates)}\n\nKnown file paths:\n{json.dumps(snapshot.get('file_tree', [])[:300])}"""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = await asyncio.to_thread(client.models.generate_content, model="gemini-3.5-flash", contents=prompt)
            text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            insights = json.loads(text)
            if isinstance(insights, list):
                return [item for item in insights if item.get("type") in {"warning", "info", "good"} and item.get("message")][:10]
        except Exception as error:
            logger.error("Failed to generate insights: %s", error)
        return candidates
