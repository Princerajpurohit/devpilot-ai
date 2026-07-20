from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class RepoAnalysisRequest(BaseModel):
    repo_url: str = Field(..., description="The full URL of the public GitHub repository")
    github_token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token to bypass rate limits")

class CompareRequest(BaseModel):
    urls: List[str] = Field(..., min_items=2, max_items=2, description="Exactly two repository URLs to compare")


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    analysis_id: int
    question: str = Field(..., min_length=1, max_length=4000)
    chat_history: List[ChatHistoryMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
    referenced_files: List[str]


class StoredChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class Insight(BaseModel):
    type: Literal["warning", "info", "good"]
    message: str
    file: Optional[str] = None

class RepoMetadata(BaseModel):
    owner: str
    name: str
    description: Optional[str] = None
    stars: int
    forks: int
    open_issues: int
    languages: Dict[str, float]
    license: Optional[str] = None
    created_at: str
    updated_at: str

class ScoreBreakdown(BaseModel):
    overall: int
    documentation: int
    security: int
    commits: int
    structure: int

class Deduction(BaseModel):
    category: str
    points: int
    explanation: str
    file_involved: Optional[str] = None

class DocAnalysis(BaseModel):
    score: int
    readme_exists: bool
    has_description: bool
    has_installation: bool
    has_usage: bool
    has_demo: bool
    has_screenshots: bool
    has_api_docs: bool
    has_contribution_guide: bool
    has_license_info: bool
    deductions: List[Deduction]

class CommitTimelinePoint(BaseModel):
    date: str
    count: int

class PoorCommitMessage(BaseModel):
    hash: str
    message: str
    author: str
    date: str

class CommitAnalysis(BaseModel):
    score: int
    total_commits: int
    avg_commits_per_week: float
    contributors_count: int
    poor_messages_percentage: float
    poor_messages: List[PoorCommitMessage]
    timeline: List[CommitTimelinePoint]
    deductions: List[Deduction]

class StructureAnalysis(BaseModel):
    score: int
    has_gitignore: bool
    has_license: bool
    has_docker: bool
    has_github_actions: bool
    has_tests: bool
    folder_organization_score: int
    naming_conventions_score: int
    config_files: List[str]
    deductions: List[Deduction]

class ExposedSecret(BaseModel):
    file_path: str
    line: int
    secret_type: str
    snippet: str

class DependencyVulnerability(BaseModel):
    package_name: str
    current_version: str
    severity: str
    description: str
    patched_version: Optional[str] = None
    file_path: str

class SecurityAnalysis(BaseModel):
    score: int
    secrets: List[ExposedSecret]
    vulnerabilities: List[DependencyVulnerability]
    deductions: List[Deduction]

class RoadmapItem(BaseModel):
    id: str
    title: str
    category: str
    severity: str  # High, Medium, Low
    estimated_score_gain: int
    difficulty: str  # Easy, Medium, Hard
    time_estimate: str
    files_involved: List[str]
    suggested_fix: str

class RepoAnalysisResponse(BaseModel):
    id: Optional[int] = None
    repo_url: str
    timestamp: datetime
    metadata: RepoMetadata
    scores: ScoreBreakdown
    documentation: DocAnalysis
    commits: CommitAnalysis
    structure: StructureAnalysis
    security: SecurityAnalysis
    ai_assessment: str
    roadmap: List[RoadmapItem]
