import asyncio
import logging
from typing import Dict, Any, List, Optional
from app.config import settings
from app.schemas import RepoMetadata, ScoreBreakdown, DocAnalysis, CommitAnalysis, StructureAnalysis, SecurityAnalysis

logger = logging.getLogger(__name__)

class AIGenerator:
    CHAT_SYSTEM_PROMPT = """You are a senior engineer who has studied this repository. Answer referencing exact file paths from the given structure. Be specific, never generic. If unsure, say so."""

    @classmethod
    async def answer_repository_question(cls, context: str, question: str, chat_history: List[Dict[str, str]]) -> str:
        if not settings.GEMINI_API_KEY:
            return "Gemini is not configured for this deployment, so I cannot provide a repository-grounded answer."

        history = "\n".join(
            f"{message.get('role', 'user').upper()}: {message.get('content', '')}"
            for message in chat_history[-12:]
        )
        prompt = f"""{cls.CHAT_SYSTEM_PROMPT}

=== REPOSITORY CONTEXT ===
{context}

=== PRIOR CONVERSATION ===
{history or "No prior conversation."}

=== QUESTION ===
{question}

Answer in concise Markdown. Only make claims supported by the repository context. When relevant, cite exact paths using backticks.
"""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as error:
            logger.error("Failed to generate repository chat response: %s", error)

        return "I could not generate a repository-grounded answer right now. Please try again."

    @classmethod
    def compile_deterministic_summary(
        cls,
        metadata: RepoMetadata,
        scores: ScoreBreakdown,
        doc: DocAnalysis,
        commits: CommitAnalysis,
        struct: StructureAnalysis,
        sec: SecurityAnalysis
    ) -> str:
        """
        Compiles a high-quality, professional, investor-ready codebase review
        using strictly deterministic rule-based analysis. Serves as a reliable fallback.
        """
        # Executive Verdict
        if scores.overall >= 80:
            verdict = "VIBRANT & MATURE"
            risk_level = "LOW"
            summary_desc = (
                f"The repository '{metadata.name}' exhibits excellent hygiene, robust developer patterns, and a "
                f"mature delivery cycle, earning an overall Intelligence Score of {scores.overall}/100. "
                "The codebase represents a solid technical asset with minimal legacy constraints, making it highly "
                "suitable for rapid scaling and institutional investment."
            )
        elif scores.overall >= 60:
            verdict = "CAPABLE BUT CONSTRAINED"
            risk_level = "MEDIUM"
            summary_desc = (
                f"The codebase for '{metadata.name}' is functional and active, scoring {scores.overall}/100. "
                "However, it displays architectural inconsistencies, documentation gaps, or lack of automated testing "
                "that could introduce technical debt and slow down engineering velocity during team expansion. "
                "Remediation of these bottlenecks is recommended to de-risk development."
            )
        else:
            verdict = "HIGH-RISK / LEVERAGED DEBT"
            risk_level = "HIGH"
            summary_desc = (
                f"The repository '{metadata.name}' reports a critical score of {scores.overall}/100. It exhibits "
                "significant deficiencies in safety controls, testing coverage, or baseline documentation. In its current "
                "state, the repository carries substantial operational risks, making it difficult to onboard new developers "
                "or run production workloads without immediate refactoring."
            )

        # Documentation Audit
        doc_details = []
        if doc.readme_exists:
            doc_details.append("✓ README.md is present and serves as the codebase entrypoint.")
            if doc.has_installation:
                doc_details.append("✓ Standard installation instructions are documented, lowering developer onboarding friction.")
            else:
                doc_details.append("✗ Missing step-by-step setup guides, which increases development setup time.")
            if doc.has_usage:
                doc_details.append("✓ Usage guidelines are provided, helping demonstrate main feature execution.")
            else:
                doc_details.append("✗ Lack of API or feature usage examples; developers must audit the code directly to understand utilization.")
        else:
            doc_details.append("✗ README.md is missing. There is zero entry documentation for the project.")

        # Commit Quality
        commit_details = []
        commit_details.append(f"- Active development history shows {commits.total_commits} commits across {commits.contributors_count} contributor(s).")
        commit_details.append(f"- The project registers {commits.avg_commits_per_week} average weekly commits, reflecting its velocity.")
        if commits.poor_messages_percentage > 10:
            commit_details.append(
                f"- A significant percentage ({commits.poor_messages_percentage}%) of commits use generic messages "
                "(e.g. 'fix', 'wip'). This reduces git auditability and complicates regression tracing."
            )
        else:
            commit_details.append("- Git message formatting is clean, displaying high developer alignment and change traceability.")

        # Structure & Hygiene
        struct_details = []
        struct_details.append("✓ .gitignore file is present." if struct.has_gitignore else "✗ Missing .gitignore: risk of committing temporary files and node_modules.")
        struct_details.append("✓ Open source LICENSE is declared." if struct.has_license else "✗ Missing LICENSE file: creates intellectual property and licensing ambiguity.")
        struct_details.append("✓ CI/CD workflows are present for automated build verification." if struct.has_github_actions else "✗ No active CI/CD configs: developer integrations are not verified automatically.")
        struct_details.append("✓ Test coverage exists in the file tree." if struct.has_tests else "✗ No automated test folder or files detected: high risk of regression bugs.")
        struct_details.append("✓ Docker containerization configurations are supported." if struct.has_docker else "✗ Docker configuration is missing: lacks unified environment reproducibility.")

        # Security Risk
        sec_details = []
        if sec.secrets:
            sec_details.append(f"✗ CRITICAL: Detected {len(sec.secrets)} instances of exposed hardcoded credentials. This is an active vulnerability.")
        else:
            sec_details.append("✓ No hardcoded secrets (API keys, Private keys) were exposed in scanned files.")
            
        if sec.vulnerabilities:
            high_v = [v for v in sec.vulnerabilities if v.severity.upper() in ["HIGH", "CRITICAL"]]
            sec_details.append(f"✗ VULNERABILITY: OSV database reports {len(sec.vulnerabilities)} vulnerable packages (including {len(high_v)} High/Critical severity issues).")
        else:
            sec_details.append("✓ Scanned dependency libraries match current vulnerability patches (no outstanding CVEs).")

        # Compile full report
        report = f"""### EXECUTIVE AUDIT SUMMARY
**Technical Valuation Rating:** {verdict}
**Overall Risk Profile:** {risk_level}

{summary_desc}

---

### METRIC ANALYSIS

#### 1. Security & Compliance
{" ".join(sec_details)}

#### 2. Documentation & Onboarding Readiness
{" ".join(doc_details)}

#### 3. Development Velocity & Version Control Hygiene
{" ".join(commit_details)}

#### 4. Architecture & Build Configuration
{" ".join(struct_details)}

---

### INVESTOR & ENGINEERING RECOMMENDATIONS
1. **Security Remediation:** {"Address exposed secrets immediately, rotate credentials, and update vulnerable package requirements." if (sec.secrets or sec.vulnerabilities) else "Maintain current patching cadences and schedule periodic dependency scans."}
2. **Quality Controls:** {"Configure unit tests and establish automated workflows inside GitHub Actions to run tests on every pull request." if (not struct.has_tests or not struct.has_github_actions) else "Verify unit test coverage meets the standard 80%+ benchmark."}
3. **Documentation:** {"Expand the README with proper API docs, usage guidelines, and build requirements to simplify future onboarding." if not doc.has_api_docs or not doc.has_usage else "Maintain current standard documentation and add screenshots for user-facing features."}
4. **Git Discipline:** {"Establish commitlint or conventional commit rules to reduce generic changes and improve repository history audit trails." if commits.poor_messages_percentage > 10 else "Maintain excellent git commit discipline; continue enforcing semantic messaging."}
"""
        return report

    @classmethod
    async def generate(
        cls,
        metadata: RepoMetadata,
        scores: ScoreBreakdown,
        doc: DocAnalysis,
        commits: CommitAnalysis,
        struct: StructureAnalysis,
        sec: SecurityAnalysis
    ) -> str:
        """
        Generate summary using Gemini if API key is provided, else fallback to deterministic summary.
        """
        deterministic_summary = cls.compile_deterministic_summary(metadata, scores, doc, commits, struct, sec)
        
        if not settings.GEMINI_API_KEY:
            logger.info("Gemini API key is not configured. Using deterministic fallback generator.")
            return deterministic_summary

        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            prompt = f"""You are a Principal Code Architect and Technical Due Diligence Auditor. Write a startup codebase review for potential investors.
Your review must be objective, professional, and investor-friendly.
You must ONLY use the actual findings listed below. Do NOT hallucinate any features, files, or facts not in the list.

=== FINDINGS ===
Repository Name: {metadata.name}
Description: {metadata.description or "No description provided."}
Overall Score: {scores.overall}/100 (Breakdown: Security={scores.security}, Documentation={scores.documentation}, Commit Quality={scores.commits}, Project Structure={scores.structure})

Documentation Check:
- README Exists: {doc.readme_exists}
- Has Installation Instructions: {doc.has_installation}
- Has Usage Examples: {doc.has_usage}
- Has API Documentation: {doc.has_api_docs}
- Has Live Demo Link: {doc.has_demo}
- Has Screenshots: {doc.has_screenshots}

Commit Analytics (Recent history):
- Total Commits Scanned: {commits.total_commits}
- Unique Contributors: {commits.contributors_count}
- Average Commits per Week: {commits.avg_commits_per_week}
- Percentage of Generic/Poor Commit Messages (e.g., 'fix', 'wip'): {commits.poor_messages_percentage}%

Project Structure & Hygiene:
- Gitignore Present: {struct.has_gitignore}
- Open Source License Declared: {struct.has_license}
- CI/CD Configurations Found: {struct.has_github_actions}
- Tests Directory/Files Detected: {struct.has_tests}
- Docker Containerization Support Found: {struct.has_docker}
- Config Files Found: {", ".join(struct.config_files) if struct.config_files else "None"}

Security Analysis:
- Number of Exposed Hardcoded Secrets: {len(sec.secrets)}
- Number of Vulnerabilities: {len(sec.vulnerabilities)} (Vulnerable Packages: {", ".join(set(v.package_name for v in sec.vulnerabilities)) if sec.vulnerabilities else "None"})

=== OUTPUT REQUIREMENTS ===
1. Provide a heading "### EXECUTIVE AUDIT SUMMARY" summarizing the technical maturity and risk level (Low, Medium, or High).
2. Create sections "### METRIC ANALYSIS" evaluating Security, Documentation, Version Control, and Architecture.
3. List actionable recommendations under "### INVESTOR & ENGINEERING RECOMMENDATIONS".
4. Make sure to reference actual metrics, files, and packages (e.g. referencing exposed secrets or specific vulnerabilities if they exist).
5. Do NOT hallucinate. If there are no secrets or vulnerabilities, explicitly state that none were found.
6. Keep the tone professional, investor-friendly, and concise. Format with markdown.
"""
            # Call Gemini
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary with Gemini: {str(e)}. Falling back to deterministic summary.")
            
        return deterministic_summary
