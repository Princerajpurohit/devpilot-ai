import re
from typing import List, Dict, Any, Optional
from app.schemas import StructureAnalysis, Deduction

class StructureAnalyzer:
    @staticmethod
    def analyze(file_tree: List[Dict[str, Any]], readme_content: Optional[str]) -> StructureAnalysis:
        """
        Analyze repository structure and hygiene.
        Weight: 20% of overall score.
        """
        deductions: List[Deduction] = []
        
        has_gitignore = False
        has_license = False
        has_docker = False
        has_github_actions = False
        has_tests = False
        has_badges = False
        
        root_files_count = 0
        spaces_filenames = []
        config_files = []
        
        # Regexes for structure checks
        config_pattern = re.compile(
            r"^(tsconfig\.json|package\.json|requirements\.txt|setup\.py|pyproject\.toml|"
            r"vite\.config\.[jt]s|webpack\.config\.js|\.eslintrc\..*|\.prettierrc\..*|"
            r"go\.mod|Cargo\.toml|composer\.json|Makefile|gemfile|angular\.json)$", re.IGNORECASE
        )
        
        test_pattern = re.compile(
            r"(^|/)(test|tests|__tests__|spec|specs)(/|$)|"
            r"\.(test|spec)\.(js|ts|jsx|tsx|py|go|rb|java|cpp|cs)$|"
            r"_test\.(py|go)$", re.IGNORECASE
        )
        
        # 1. Scan the file tree
        for item in file_tree:
            path = item.get("path", "")
            path_lower = path.lower()
            item_type = item.get("type", "")
            
            # Check for root files
            is_root = "/" not in path
            
            if item_type == "blob":
                if is_root:
                    root_files_count += 1
                    
                    # Gitignore
                    if path_lower == ".gitignore":
                        has_gitignore = True
                    # License
                    if "license" in path_lower or "licence" in path_lower:
                        has_license = True
                    # Docker
                    if path_lower in ["dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"]:
                        has_docker = True
                        
                    # Config files
                    if config_pattern.match(path):
                        config_files.append(path)
                
                # Check for file naming conventions (spaces in names)
                filename = path.split("/")[-1]
                if " " in filename and not filename.startswith("."):
                    # Only check code/script files, skip logs, docs, assets
                    if filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".h", ".sh", ".cs", ".rb", ".php")):
                        spaces_filenames.append(path)
                        
            elif item_type == "tree":
                # GitHub Actions Check
                if path_lower.startswith(".github/workflows"):
                    has_github_actions = True
                    
            # Tests Check (files or folders matching patterns)
            if test_pattern.search(path):
                has_tests = True
                
        # 2. Check README for badges if readme exists
        if readme_content:
            badge_pattern = r"\[\!\[.*?\]\(.*?\)\]\(.*?\)|\bshields\.io\b|https://img\.shields\.io"
            has_badges = bool(re.search(badge_pattern, readme_content))
            
        # Scoring logic
        score = 100
        
        # Gitignore: 15 pts
        if not has_gitignore:
            score -= 15
            deductions.append(Deduction(
                category="Project Structure",
                points=15,
                explanation="Missing .gitignore file in the repository root. A .gitignore file prevents local environment configs, build files, and node_modules from polluting the version control.",
                file_involved=".gitignore"
            ))
            
        # License: 15 pts
        if not has_license:
            score -= 15
            deductions.append(Deduction(
                category="Project Structure",
                points=15,
                explanation="No LICENSE file was detected at the repository root. Without an explicit open-source license, users may not copy, distribute, or modify the software safely.",
                file_involved="LICENSE"
            ))
            
        # GitHub Actions: 15 pts
        if not has_github_actions:
            score -= 15
            deductions.append(Deduction(
                category="Project Structure",
                points=15,
                explanation="No CI/CD configuration files (such as GitHub Actions under .github/workflows/) were found. Automated integrations prevent build regression.",
                file_involved=None
            ))
            
        # Tests: 20 pts
        if not has_tests:
            score -= 20
            deductions.append(Deduction(
                category="Project Structure",
                points=20,
                explanation="No tests folder (like 'test/' or 'tests/') or test script files were detected. Creating automated tests guarantees that code modifications do not break functionality.",
                file_involved=None
            ))
            
        # Docker: 10 pts
        if not has_docker:
            score -= 10
            deductions.append(Deduction(
                category="Project Structure",
                points=10,
                explanation="No Docker configuration was detected. Providing a Dockerfile or docker-compose setup allows developers to spin up the application in a unified environment.",
                file_involved="Dockerfile"
            ))
            
        # Badges: 5 pts
        if not has_badges:
            score -= 5
            deductions.append(Deduction(
                category="Project Structure",
                points=5,
                explanation="No status badges were detected in your README. Add shields.io badges representing build success, test coverage, and release versions to boost developer trust.",
                file_involved="README.md"
            ))
            
        # Folder Cleanliness (Source files in root): 10 pts
        # If there are a lot of source code files in root (we filter config/md files)
        # Check files ending in code extensions in root
        root_code_files = [
            item.get("path") for item in file_tree
            if "/" not in item.get("path", "")
            and item.get("type") == "blob"
            and item.get("path", "").endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".cs", ".rb", ".php"))
        ]
        if len(root_code_files) > 10:
            score -= 10
            deductions.append(Deduction(
                category="Project Structure",
                points=10,
                explanation=f"Over 10 source code files ({len(root_code_files)}) were detected directly in the root directory. Clean the root directory by organizing sources into folder directories like 'src/', 'lib/', or 'app/'.",
                file_involved=root_code_files[0]
            ))
            
        # Naming Conventions (Spaces in files): 10 pts
        if spaces_filenames:
            score -= 10
            deductions.append(Deduction(
                category="Project Structure",
                points=10,
                explanation=f"Exposed file paths containing spaces were detected (e.g. '{spaces_filenames[0]}'). Rename source files using kebab-case or snake_case to prevent import and build resolution failures.",
                file_involved=spaces_filenames[0]
            ))

        return StructureAnalysis(
            score=max(0, score),
            has_gitignore=has_gitignore,
            has_license=has_license,
            has_docker=has_docker,
            has_github_actions=has_github_actions,
            has_tests=has_tests,
            folder_organization_score=100 if len(root_code_files) <= 10 else 90,
            naming_conventions_score=100 if not spaces_filenames else 90,
            config_files=config_files,
            deductions=deductions
        )
