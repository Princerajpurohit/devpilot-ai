import re
from typing import Dict, Any, List, Optional
from app.schemas import DocAnalysis, Deduction

class DocAnalyzer:
    @staticmethod
    def analyze(readme_content: Optional[str]) -> DocAnalysis:
        """
        Analyze README content and compute documentation score and deductions.
        Weight: 30% of overall score.
        """
        deductions: List[Deduction] = []
        
        if not readme_content:
            deductions.append(Deduction(
                category="Documentation",
                points=100,
                explanation="README.md is missing from the repository. A README is critical for explaining the project, guiding installation, and helping users get started.",
                file_involved="README.md"
            ))
            return DocAnalysis(
                score=0,
                readme_exists=False,
                has_description=False,
                has_installation=False,
                has_usage=False,
                has_demo=False,
                has_screenshots=False,
                has_api_docs=False,
                has_contribution_guide=False,
                has_license_info=False,
                deductions=deductions
            )

        readme_lower = readme_content.lower()
        
        # 1. Opening Description
        # Check if there is some textual content besides just headers
        lines = [line.strip() for line in readme_content.split("\n") if line.strip()]
        has_description = len(lines) > 2  # Has more than just title and one line
        
        # 2. Installation Guide
        install_pattern = r"(#+\s+.*(?:install|setup|get.*started|run|deploy|dependency|prerequisite|build))"
        has_installation = bool(re.search(install_pattern, readme_lower))
        
        # 3. Usage Section
        usage_pattern = r"(#+\s+.*(?:usage|example|how.*to.*use|tutorial|quickstart|configure|configuration))"
        has_usage = bool(re.search(usage_pattern, readme_lower))
        
        # 4. Live Demo
        # Check for links with demo, deploy, vercel, netlify, heroku, github.io, etc.
        demo_pattern = r"https?://[^\s)]*(?:demo|live|vercel|netlify|heroku|github\.io|pages)[^\s)]*"
        has_demo = bool(re.search(demo_pattern, readme_lower)) or "live demo" in readme_lower
        
        # 5. Screenshots
        # Markdown image format: ![desc](url) or <img> tag
        screenshot_pattern = r"!\[.*?\]\(.*?\)|<img\s+.*?src=.*?>"
        has_screenshots = bool(re.search(screenshot_pattern, readme_content))
        
        # 6. API Documentation
        api_pattern = r"(#+\s+.*(?:api|endpoint|route|reference|method|sdk|schema|interface))"
        has_api_docs = bool(re.search(api_pattern, readme_lower))
        
        # 7. Contribution Guide
        contribute_pattern = r"(#+\s+.*(?:contribut|develop|guideline|pull.*request|issue|setup.*dev))"
        has_contribution_guide = bool(re.search(contribute_pattern, readme_lower)) or "contribute" in readme_lower
        
        # 8. License Info
        license_pattern = r"(#+\s+.*(?:license|licence|copyright))|license"
        has_license_info = bool(re.search(license_pattern, readme_lower))
        
        # Calculate scores
        score = 100
        
        if not has_description:
            score -= 15
            deductions.append(Deduction(
                category="Documentation",
                points=15,
                explanation="The README has a very short or missing opening description. A clear introduction explains what the project does and its core value proposition.",
                file_involved="README.md"
            ))
            
        if not has_installation:
            score -= 15
            deductions.append(Deduction(
                category="Documentation",
                points=15,
                explanation="No clear installation or setup guide was detected. Adding step-by-step instructions (e.g. commands, prerequisites) helps developers run the codebase.",
                file_involved="README.md"
            ))
            
        if not has_usage:
            score -= 15
            deductions.append(Deduction(
                category="Documentation",
                points=15,
                explanation="Missing a dedicated 'Usage' or 'Examples' section. Providing basic code snippets or CLI invocations shows users how to interact with the project.",
                file_involved="README.md"
            ))
            
        if not has_demo:
            score -= 10
            deductions.append(Deduction(
                category="Documentation",
                points=10,
                explanation="No live demo URL or hosting link was found. A demo helps users quickly evaluate the project without installing it locally.",
                file_involved="README.md"
            ))
            
        if not has_screenshots:
            score -= 10
            deductions.append(Deduction(
                category="Documentation",
                points=10,
                explanation="No screenshots, diagrams, or visual assets were detected. Adding images or GIF walkthroughs increases readability and visual appeal.",
                file_involved="README.md"
            ))
            
        if not has_api_docs:
            score -= 15
            deductions.append(Deduction(
                category="Documentation",
                points=15,
                explanation="Missing API reference or detailed developer endpoint documentation. Projects with interfaces, web endpoints, or libraries should document their APIs.",
                file_involved="README.md"
            ))
            
        if not has_contribution_guide:
            score -= 10
            deductions.append(Deduction(
                category="Documentation",
                points=10,
                explanation="No contribution guide or contributing section was found. A guide outlines coding styles and pull request workflows to encourage community participation.",
                file_involved="README.md"
            ))
            
        if not has_license_info:
            score -= 10
            deductions.append(Deduction(
                category="Documentation",
                points=10,
                explanation="No license section found in the README. Clearly stating the project's license in the README prevents legal ambiguity for contributors and organizations.",
                file_involved="README.md"
            ))

        return DocAnalysis(
            score=max(0, score),
            readme_exists=True,
            has_description=has_description,
            has_installation=has_installation,
            has_usage=has_usage,
            has_demo=has_demo,
            has_screenshots=has_screenshots,
            has_api_docs=has_api_docs,
            has_contribution_guide=has_contribution_guide,
            has_license_info=has_license_info,
            deductions=deductions
        )
