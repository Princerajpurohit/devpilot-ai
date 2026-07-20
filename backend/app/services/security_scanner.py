import re
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from app.schemas import SecurityAnalysis, ExposedSecret, DependencyVulnerability, Deduction

class SecurityScanner:
    # Regex patterns for detecting common secrets
    SECRET_PATTERNS = {
        "AWS API Key": r"\b(AKIA[0-9A-Z]{16})\b",
        "Private Key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "Firebase API Key": r"\b(AIzaSy[0-9A-Za-z\-_]{33})\b",
        "Generic Secret/Token": r"(?i)\b(api_key|secret|token|password|passwd|jwt_secret|aws_secret|token_secret)\b\s*[:=]\s*['\"]([0-9a-zA-Z\-_]{16,})['\"]"
    }

    @classmethod
    def scan_for_secrets(cls, file_path: str, content: str) -> List[ExposedSecret]:
        """Scan a file's content for secrets using pre-defined regex patterns."""
        secrets_found = []
        if not content:
            return secrets_found
            
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            # Skip comments if possible, but keep scanning robust
            for secret_type, pattern in cls.SECRET_PATTERNS.items():
                matches = re.findall(pattern, line)
                if matches:
                    # For patterns with multiple capture groups (like Generic Secret)
                    match_val = matches[0]
                    if isinstance(match_val, tuple):
                        match_val = match_val[1] # Take the actual value
                    
                    # Ignore obvious placeholders or mocks
                    val_lower = match_val.lower()
                    if any(p in val_lower for p in ["placeholder", "mock", "test", "your_", "example", "dummy"]):
                        continue
                        
                    # Truncate secret for safety in UI
                    snippet = line.strip()
                    if len(match_val) > 4:
                        masked = match_val[:4] + "********" + match_val[-4:]
                        snippet = snippet.replace(match_val, masked)
                        
                    secrets_found.append(ExposedSecret(
                        file_path=file_path,
                        line=line_num,
                        secret_type=secret_type,
                        snippet=snippet
                    ))
        return secrets_found

    @staticmethod
    def parse_package_json(content: str) -> List[Tuple[str, str]]:
        """Parse dependencies from package.json content."""
        deps = []
        try:
            data = json.loads(content)
            # Combine dependencies and devDependencies
            raw_deps = {}
            if "dependencies" in data and isinstance(data["dependencies"], dict):
                raw_deps.update(data["dependencies"])
            if "devDependencies" in data and isinstance(data["devDependencies"], dict):
                raw_deps.update(data["devDependencies"])
                
            for pkg, ver_range in raw_deps.items():
                # Extract simple semantic version (e.g. ^1.2.3 -> 1.2.3)
                ver_match = re.search(r"(\d+\.\d+\.\d+)", str(ver_range))
                if ver_match:
                    deps.append((pkg, ver_match.group(1)))
        except Exception:
            pass
        return deps

    @staticmethod
    def parse_requirements_txt(content: str) -> List[Tuple[str, str]]:
        """Parse dependencies from requirements.txt content."""
        deps = []
        if not content:
            return deps
            
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # e.g., requests==2.25.1 or flask>=2.0
            match = re.split(r"==|>=|<=|~=", line)
            if len(match) >= 2:
                pkg = match[0].strip()
                ver = match[1].strip()
                # Clean up version comments or tags
                ver = re.split(r"\s|#", ver)[0]
                deps.append((pkg, ver))
        return deps

    @classmethod
    async def query_osv_api(cls, package_name: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Queries OSV API for vulnerabilities in a package and version."""
        url = "https://api.osv.dev/v1/query"
        payload = {
            "version": version,
            "package": {
                "name": package_name,
                "ecosystem": ecosystem
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("vulns", [])
        except Exception:
            pass
        return []

    @classmethod
    async def scan(cls, github_client: Any, owner: str, repo: str, file_tree: List[Dict[str, Any]], branch: str = "main") -> SecurityAnalysis:
        """
        Analyze code files for credentials and dependencies for OSV CVEs.
        Weight: 30% of overall score.
        """
        secrets: List[ExposedSecret] = []
        vulnerabilities: List[DependencyVulnerability] = []
        deductions: List[Deduction] = []
        
        # 1. Identify files to scan for secrets (configs and some code files)
        scan_paths = []
        manifest_files = {} # Keep content of packages/requirements
        
        for item in file_tree:
            path = item.get("path", "")
            path_lower = path.lower()
            if item.get("type") == "blob":
                # Find dependency files
                if path_lower.endswith("package.json"):
                    scan_paths.append(path)
                elif path_lower.endswith("requirements.txt"):
                    scan_paths.append(path)
                # Find common config and code files
                elif any(path_lower.endswith(ext) for ext in [".env", ".env.example", ".env.local", "config.py", "settings.py", "secrets.json"]):
                    scan_paths.append(path)
                # Add first 15 core source code files to scan for hardcoded secrets
                elif len(scan_paths) < 30 and any(path_lower.endswith(ext) for ext in [".js", ".ts", ".py", ".go", ".java", ".sh"]):
                    scan_paths.append(path)

        # Fetch contents of all marked paths in parallel
        contents_dict = await github_client.fetch_multiple_files(owner, repo, scan_paths, branch)
        
        # Scan files for secrets
        for path, content in contents_dict.items():
            if not content:
                continue
            
            # Store dependency contents for later parsing
            if path.endswith("package.json") or path.endswith("requirements.txt"):
                manifest_files[path] = content
                
            # Perform secret scan
            secrets_found = cls.scan_for_secrets(path, content)
            secrets.extend(secrets_found)

        # 2. Parse dependencies and check via OSV API
        dep_tasks = []
        for path, content in manifest_files.items():
            if path.endswith("package.json"):
                npm_deps = cls.parse_package_json(content)
                # Limit dependencies to first 15 to keep query times reasonable
                for pkg, ver in npm_deps[:15]:
                    dep_tasks.append((pkg, ver, "npm", path))
            elif path.endswith("requirements.txt"):
                pypi_deps = cls.parse_requirements_txt(content)
                for pkg, ver in pypi_deps[:15]:
                    dep_tasks.append((pkg, ver, "PyPI", path))

        # Perform OSV Queries concurrently
        if dep_tasks:
            queries = [
                cls.query_osv_api(task[0], task[1], task[2])
                for task in dep_tasks
            ]
            results = await asyncio.gather(*queries, return_exceptions=True)
            
            for task, res in zip(dep_tasks, results):
                if isinstance(res, Exception) or not res:
                    continue
                
                pkg_name, ver, ecosystem, path = task
                for vuln in res:
                    # Extract vulnerability details
                    vuln_id = vuln.get("id", "Vulnerability")
                    summary = vuln.get("summary", vuln.get("details", "Vulnerability detected"))
                    if len(summary) > 150:
                        summary = summary[:147] + "..."
                        
                    # Severity parsing
                    severity = "Medium"
                    database_specific = vuln.get("database_specific", {})
                    if database_specific:
                        cvss = database_specific.get("cvss", {})
                        if isinstance(cvss, dict):
                            severity = cvss.get("severity", "Medium")
                    
                    # Patched version search
                    patched = None
                    for affected in vuln.get("affected", []):
                        if affected.get("package", {}).get("name") == pkg_name:
                            for ranges in affected.get("ranges", []):
                                for event in ranges.get("events", []):
                                    if "fixed" in event:
                                        patched = event["fixed"]
                                        break
                                        
                    vulnerabilities.append(DependencyVulnerability(
                        package_name=pkg_name,
                        current_version=ver,
                        severity=severity,
                        description=f"{vuln_id}: {summary}",
                        patched_version=patched,
                        file_path=path
                    ))

        # Calculate security score (out of 100)
        score = 100
        
        # Deduct for hardcoded secrets
        if secrets:
            # Deduct 25 points if secrets are found
            secret_deduction = min(50, len(secrets) * 25)
            score -= secret_deduction
            deductions.append(Deduction(
                category="Security",
                points=secret_deduction,
                explanation=f"Detected {len(secrets)} occurrences of hardcoded secrets (API keys, Private Keys, or Secrets) in the repository source code. Hardcoded credentials are a major risk; move them to environment variables immediately.",
                file_involved=secrets[0].file_path
            ))

        # Deduct for vulnerabilities
        high_vulns = [v for v in vulnerabilities if v.severity.upper() in ["HIGH", "CRITICAL"]]
        med_vulns = [v for v in vulnerabilities if v.severity.upper() in ["MEDIUM", "LOW", "MODERATE"]]
        
        if high_vulns:
            high_deduct = min(40, len(high_vulns) * 15)
            score -= high_deduct
            deductions.append(Deduction(
                category="Security",
                points=high_deduct,
                explanation=f"Detected {len(high_vulns)} High or Critical severity vulnerabilities in package dependencies. Upgrade these packages immediately to patch known vulnerabilities.",
                file_involved=high_vulns[0].file_path
            ))

        if med_vulns:
            med_deduct = min(20, len(med_vulns) * 5)
            score -= med_deduct
            deductions.append(Deduction(
                category="Security",
                points=med_deduct,
                explanation=f"Detected {len(med_vulns)} Medium or Low severity vulnerabilities in dependencies. Keep libraries up to date to minimize CVE exposure.",
                file_involved=med_vulns[0].file_path
            ))

        return SecurityAnalysis(
            score=max(0, score),
            secrets=secrets,
            vulnerabilities=vulnerabilities,
            deductions=deductions
        )
