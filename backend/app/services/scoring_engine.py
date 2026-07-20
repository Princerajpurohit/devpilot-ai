from typing import List, Dict, Any
from app.schemas import ScoreBreakdown, Deduction, RoadmapItem, RepoAnalysisResponse
from app.schemas import DocAnalysis, CommitAnalysis, StructureAnalysis, SecurityAnalysis

class ScoringEngine:
    @staticmethod
    def generate_roadmap(
        doc: DocAnalysis,
        commits: CommitAnalysis,
        struct: StructureAnalysis,
        sec: SecurityAnalysis
    ) -> List[RoadmapItem]:
        """
        Builds a ranked roadmap from all deductions, sorted by impact (estimated score gain).
        """
        roadmap: List[RoadmapItem] = []
        item_id = 1
        
        # Helper to maps deductions to roadmap items
        def add_roadmap_items(deductions: List[Deduction], category: str):
            nonlocal item_id
            for d in deductions:
                # Determine severity, difficulty, time, and suggestions based on category & points
                files = [d.file_involved] if d.file_involved else []
                
                # Default settings
                difficulty = "Medium"
                time_est = "1-2 hours"
                suggested_fix = d.explanation
                
                if category == "Security":
                    severity = "High"
                    if "secrets" in d.explanation.lower():
                        difficulty = "Easy"
                        time_est = "30 mins"
                        suggested_fix = (
                            "Identify the exposed credential in the files, delete it from version history "
                            "using git-filter-repo or BFG Repo-Cleaner, rotate the credential immediately, "
                            "and store it in an environment variable loaded via dotenv."
                        )
                    else:
                        difficulty = "Medium"
                        time_est = "1 hour"
                        suggested_fix = (
                            "Examine package.json or requirements.txt and identify the outdated libraries. "
                            "Run package manager upgrade commands (e.g. 'npm install package@latest' or "
                            "updating requirements.txt version pins) to apply security patches."
                        )
                elif category == "Documentation":
                    severity = "Medium" if d.points >= 15 else "Low"
                    difficulty = "Easy"
                    time_est = "15-30 mins"
                    
                    if not doc.readme_exists:
                        suggested_fix = "Create a README.md file in the repository root containing the project title, installation, and basic commands."
                    elif "description" in d.explanation.lower():
                        suggested_fix = "Add a descriptive opening paragraph to your README.md detailing the project's purpose and core value proposition."
                    elif "installation" in d.explanation.lower():
                        suggested_fix = "Add an 'Installation' or 'Getting Started' markdown section with commands like 'npm install' or 'pip install -r requirements.txt'."
                    elif "usage" in d.explanation.lower():
                        suggested_fix = "Add a 'Usage' section in the README with code snippet examples showing how to import, configure, and execute the application."
                    elif "api" in d.explanation.lower():
                        suggested_fix = "Document public endpoints, classes, or parameters. List HTTP methods, URI parameters, and response structures in the README or a dedicated docs folder."
                    elif "demo" in d.explanation.lower():
                        suggested_fix = "Deploy the application to Vercel, Netlify, Github Pages, or Heroku and place the live hyperlink at the top of your README."
                    elif "screenshot" in d.explanation.lower():
                        suggested_fix = "Take screenshots of the app UI or CLI tools, upload them to your repository (e.g. in an 'assets/' directory), and reference them in your README using Markdown image tags."
                    elif "contribution" in d.explanation.lower():
                        suggested_fix = "Create a CONTRIBUTING.md file or add a 'Contributing' section to outline the pull request process, coding guidelines, and local dev setup."
                    elif "license" in d.explanation.lower():
                        suggested_fix = "Add a 'License' section to the README (e.g., MIT, Apache 2.0) referencing the LICENSE file to clarify permissions."
                    else:
                        suggested_fix = f"Update your README.md to add details regarding: {d.explanation.lower()}"
                
                elif category == "Project Structure":
                    severity = "Medium" if d.points >= 15 else "Low"
                    if ".gitignore" in d.explanation.lower():
                        difficulty = "Easy"
                        time_est = "10 mins"
                        suggested_fix = "Create a '.gitignore' file at the repository root. Populating it with standard templates for your language environment (e.g. node_modules, .env, __pycache__)."
                    elif "license" in d.explanation.lower():
                        difficulty = "Easy"
                        time_est = "10 mins"
                        suggested_fix = "Add a LICENSE file (e.g., MIT, Apache 2.0) at the root directory of your project. GitHub provides template dialogs to auto-generate these."
                    elif "ci/cd" in d.explanation.lower() or "actions" in d.explanation.lower():
                        difficulty = "Medium"
                        time_est = "1 hour"
                        suggested_fix = "Add a GitHub Action workflow file in '.github/workflows/ci.yml' that runs automated checks (linting, tests) on pull requests and main commits."
                    elif "tests" in d.explanation.lower():
                        difficulty = "Medium"
                        time_est = "2-4 hours"
                        suggested_fix = "Set up a test suite using frameworks like Jest, PyTest, or Vitest. Write tests within a 'tests/' folder to validate core business logic."
                    elif "docker" in d.explanation.lower():
                        difficulty = "Medium"
                        time_est = "1 hour"
                        suggested_fix = "Create a 'Dockerfile' in the root directory to containerize the app, exposing the required port and copying dependencies."
                    else:
                        difficulty = "Easy"
                        time_est = "30 mins"
                        suggested_fix = d.explanation
                
                else: # Commit Quality
                    severity = "Low"
                    difficulty = "Medium"
                    time_est = "Ongoing"
                    suggested_fix = (
                        "Introduce Conventional Commits guidelines to the project (e.g. prefixing messages with "
                        "'feat:', 'fix:', 'chore:', 'docs:'). You can set up Husky and commitlint to enforce "
                        "this policy before commits are created."
                    )

                # Weight-adjusted score gain: the roadmap is shown to the user,
                # we present the raw category points deducted to show the direct gain from fixing it
                roadmap.append(RoadmapItem(
                    id=f"RM-{item_id:03d}",
                    title=f"Fix {category} issue: {d.explanation.split('.')[0]}",
                    category=category,
                    severity=severity,
                    estimated_score_gain=d.points,
                    difficulty=difficulty,
                    time_estimate=time_est,
                    files_involved=files,
                    suggested_fix=suggested_fix
                ))
                item_id += 1

        add_roadmap_items(sec.deductions, "Security")
        add_roadmap_items(doc.deductions, "Documentation")
        add_roadmap_items(struct.deductions, "Project Structure")
        add_roadmap_items(commits.deductions, "Commit Quality")

        # Sort by impact: highest score gain first.
        # If score gain is equal, sort by severity (High -> Medium -> Low).
        severity_order = {"High": 3, "Medium": 2, "Low": 1}
        roadmap.sort(
            key=lambda x: (x.estimated_score_gain, severity_order.get(x.severity, 0)),
            reverse=True
        )
        return roadmap

    @classmethod
    def calculate_scores(
        cls,
        doc: DocAnalysis,
        commits: CommitAnalysis,
        struct: StructureAnalysis,
        sec: SecurityAnalysis
    ) -> ScoreBreakdown:
        """
        Calculate weighted overall repository score.
        Formula:
        Security: 30%
        Documentation: 30%
        Commit Quality: 20%
        Structure: 20%
        """
        sec_w = sec.score * 0.30
        doc_w = doc.score * 0.30
        commits_w = commits.score * 0.20
        struct_w = struct.score * 0.20
        
        overall = round(sec_w + doc_w + commits_w + struct_w)
        
        return ScoreBreakdown(
            overall=max(0, min(100, overall)),
            documentation=doc.score,
            security=sec.score,
            commits=commits.score,
            structure=struct.score
        )
