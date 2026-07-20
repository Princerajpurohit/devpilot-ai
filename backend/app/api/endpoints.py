import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.services.github_client import GitHubClient
from app.services.doc_analyzer import DocAnalyzer
from app.services.commit_analyzer import CommitAnalyzer
from app.services.structure_analyzer import StructureAnalyzer
from app.services.security_scanner import SecurityScanner
from app.services.scoring_engine import ScoringEngine
from app.services.ai_generator import AIGenerator
from app.services.pdf_generator import PDFGenerator
from app.services.insight_generator import InsightGenerator

router = APIRouter()

KEY_CHAT_FILES = {
    "readme.md", "package.json", "pyproject.toml", "requirements.txt", "dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    "next.config.js", "next.config.ts", "vite.config.ts", "tsconfig.json",
    "main.py", "app.py", "manage.py", "server.js", "server.ts", "index.js", "index.ts",
}


def select_chat_context_paths(file_tree: List[Dict[str, Any]]) -> List[str]:
    blobs = [item for item in file_tree if item.get("type") == "blob" and item.get("path")]
    selected = []
    for item in blobs:
        path = item["path"]
        filename = path.rsplit("/", 1)[-1].lower()
        is_root_entry = "/" not in path and filename in KEY_CHAT_FILES
        is_source_entry = filename in {"main.py", "app.py", "server.py", "index.js", "index.ts", "main.ts", "main.js"}
        if (is_root_entry or is_source_entry) and item.get("size", 0) <= 50000:
            selected.append(path)
        if len(selected) >= 12:
            break
    return selected


async def build_chat_context_snapshot(
    client: GitHubClient,
    owner: str,
    repo_name: str,
    branch: str,
    file_tree: List[Dict[str, Any]],
    languages: Dict[str, float],
    readme_content: str | None,
) -> Dict[str, Any]:
    selected_paths = select_chat_context_paths(file_tree)
    contents = await client.fetch_multiple_files(owner, repo_name, selected_paths, branch)
    if readme_content:
        readme_path = next((path for path in selected_paths if path.lower() == "readme.md"), "README.md")
        contents[readme_path] = readme_content

    return {
        "languages": languages,
        "file_tree": [
            {"path": item.get("path"), "size": item.get("size", 0)}
            for item in file_tree if item.get("type") == "blob" and item.get("path")
        ],
        "source_files": {path: content[:12000] for path, content in contents.items() if content},
    }


def compile_chat_context(snapshot: Dict[str, Any]) -> str:
    file_tree = [item.get("path") if isinstance(item, dict) else item for item in snapshot.get("file_tree", [])[:500]]
    source_sections = "\n\n".join(
        f"--- {path} ---\n{content}"
        for path, content in snapshot.get("source_files", {}).items()
    )
    return (
        f"Languages: {json.dumps(snapshot.get('languages', {}))}\n\n"
        f"Repository file structure:\n" + "\n".join(file_tree) +
        f"\n\nSelected source and configuration files:\n{source_sections}"
    )


def referenced_files_from_answer(answer: str, snapshot: Dict[str, Any]) -> List[str]:
    paths = [item.get("path") if isinstance(item, dict) else item for item in snapshot.get("file_tree", [])]
    return [path for path in paths if path in answer][:12]

async def run_full_analysis(repo_url: str, github_token: str = None) -> Tuple[schemas.RepoAnalysisResponse, Dict[str, Any]]:
    """Executes all analyzers concurrently and scores the repo."""
    try:
        # Parse owner and repo
        owner, repo_name = GitHubClient.parse_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    client = GitHubClient(token=github_token)
    
    try:
        # 1. Fetch Repository General Data
        meta_raw = await client.get_repo_data(owner, repo_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not access repository: {str(e)}")

    default_branch = meta_raw.get("default_branch", "main")
    
    # 2. Concurrently fetch languages, commits, file tree, and main files (README, package.json, requirements.txt)
    # We will gather these calls to optimize performance
    tasks = [
        client.get_languages(owner, repo_name),
        client.get_commits(owner, repo_name, limit=100),
        client.get_file_tree(owner, repo_name, branch=default_branch),
        client.get_file_content(owner, repo_name, "README.md", branch=default_branch),
    ]
    
    languages, commits, file_tree, readme_content = await asyncio.gather(*tasks)
    
    # Check other variants if README.md not found
    if not readme_content:
        for alternative in ["readme.md", "README.txt", "Readme.md", "README"]:
            readme_content = await client.get_file_content(owner, repo_name, alternative, branch=default_branch)
            if readme_content:
                break
                
    # Normalize languages representation
    total_bytes = sum(languages.values()) if languages else 1
    languages_pct = {k: round((v / total_bytes) * 100, 1) for k, v in languages.items()}
    chat_context = await build_chat_context_snapshot(
        client, owner, repo_name, default_branch, file_tree, languages_pct, readme_content
    )
    
    # Compile schemas metadata
    metadata = schemas.RepoMetadata(
        owner=owner,
        name=repo_name,
        description=meta_raw.get("description"),
        stars=meta_raw.get("stargazers_count", 0),
        forks=meta_raw.get("forks_count", 0),
        open_issues=meta_raw.get("open_issues_count", 0),
        languages=languages_pct,
        license=meta_raw.get("license", {}).get("spdx_id") if meta_raw.get("license") else None,
        created_at=meta_raw.get("created_at", ""),
        updated_at=meta_raw.get("updated_at", "")
    )
    
    # Run analysis tasks
    # Security scanner requires await as it queries external OSV API
    sec_task = SecurityScanner.scan(client, owner, repo_name, file_tree, branch=default_branch)
    
    # Sync engines (they operate on fetched structures)
    doc_analysis = DocAnalyzer.analyze(readme_content)
    commit_analysis = CommitAnalyzer.analyze(commits)
    struct_analysis = StructureAnalyzer.analyze(file_tree, readme_content)
    
    # Resolve security scanning
    sec_analysis = await sec_task
    
    # 3. Calculate Scores & Fix-it Roadmap
    scores = ScoringEngine.calculate_scores(
        doc=doc_analysis,
        commits=commit_analysis,
        struct=struct_analysis,
        sec=sec_analysis
    )
    
    roadmap = ScoringEngine.generate_roadmap(
        doc=doc_analysis,
        commits=commit_analysis,
        struct=struct_analysis,
        sec=sec_analysis
    )
    
    # 4. Invoke AI executive summary (with deterministic fallback)
    ai_assessment = await AIGenerator.generate(
        metadata=metadata,
        scores=scores,
        doc=doc_analysis,
        commits=commit_analysis,
        struct=struct_analysis,
        sec=sec_analysis
    )
    
    # Construct response
    return schemas.RepoAnalysisResponse(
        repo_url=repo_url,
        timestamp=datetime.utcnow(),
        metadata=metadata,
        scores=scores,
        documentation=doc_analysis,
        commits=commit_analysis,
        structure=struct_analysis,
        security=sec_analysis,
        ai_assessment=ai_assessment,
        roadmap=roadmap
    ), chat_context

@router.post("/analyze", response_model=schemas.RepoAnalysisResponse)
async def analyze_repository(request: schemas.RepoAnalysisRequest, db: Session = Depends(get_db)):
    """
    Submits a GitHub repo URL for complete intelligence scoring.
    Checks the SQLite database for a valid cached analysis first.
    """
    cleaned_url = request.repo_url.strip().lower()
    
    # Check cache freshness (e.g., within settings.CACHE_EXPIRY_HOURS)
    cutoff = datetime.utcnow() - timedelta(hours=settings.CACHE_EXPIRY_HOURS)
    cached = db.query(models.RepositoryAnalysis).filter(
        models.RepositoryAnalysis.repo_url == cleaned_url,
        models.RepositoryAnalysis.timestamp >= cutoff
    ).order_by(models.RepositoryAnalysis.timestamp.desc()).first()
    
    if cached:
        try:
            res_dict = json.loads(cached.analysis_json)
            res_dict["id"] = cached.id
            return res_dict
        except Exception:
            pass # Cached JSON corruption; run fresh scan
            
    # Run full analysis pipeline
    analysis_res, chat_context = await run_full_analysis(request.repo_url, request.github_token)
    
    # Generate ReportLab PDF binary
    try:
        pdf_bytes = PDFGenerator.generate(analysis_res)
    except Exception as e:
        pdf_bytes = None
        
    # Save to SQLite Database for caching
    db_entry = models.RepositoryAnalysis(
        repo_url=cleaned_url,
        owner=analysis_res.metadata.owner,
        repo_name=analysis_res.metadata.name,
        timestamp=analysis_res.timestamp,
        score=analysis_res.scores.overall,
        documentation_score=analysis_res.scores.documentation,
        security_score=analysis_res.scores.security,
        commit_score=analysis_res.scores.commits,
        structure_score=analysis_res.scores.structure,
        analysis_json=analysis_res.json(),
        chat_context_json=json.dumps(chat_context),
        pdf_report=pdf_bytes
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    # Append the DB ID to the response
    analysis_res.id = db_entry.id
    return analysis_res


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_repository(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    analysis = db.query(models.RepositoryAnalysis).filter(
        models.RepositoryAnalysis.id == request.analysis_id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    if not analysis.chat_context_json:
        raise HTTPException(
            status_code=409,
            detail="This analysis predates repository chat. Re-analyze the repository to create its stored chat context."
        )

    try:
        snapshot = json.loads(analysis.chat_context_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored repository chat context is invalid")

    answer = await AIGenerator.answer_repository_question(
        context=compile_chat_context(snapshot),
        question=request.question,
        chat_history=[message.model_dump() for message in request.chat_history],
    )
    db.add_all([
        models.ChatMessage(analysis_id=analysis.id, role="user", content=request.question),
        models.ChatMessage(analysis_id=analysis.id, role="assistant", content=answer),
    ])
    db.commit()
    return schemas.ChatResponse(
        answer=answer,
        referenced_files=referenced_files_from_answer(answer, snapshot),
    )


@router.get("/chat/{analysis_id}", response_model=List[schemas.StoredChatMessage])
async def get_chat_history(analysis_id: int, db: Session = Depends(get_db)):
    analysis_exists = db.query(models.RepositoryAnalysis.id).filter(
        models.RepositoryAnalysis.id == analysis_id
    ).first()
    if not analysis_exists:
        raise HTTPException(status_code=404, detail="Analysis ID not found")

    return db.query(models.ChatMessage).filter(
        models.ChatMessage.analysis_id == analysis_id
    ).order_by(models.ChatMessage.created_at.asc(), models.ChatMessage.id.asc()).all()


@router.get("/insights/{analysis_id}", response_model=List[schemas.Insight])
async def get_insights(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(models.RepositoryAnalysis).filter(models.RepositoryAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    if analysis.insights_json:
        return json.loads(analysis.insights_json)

    report = json.loads(analysis.analysis_json)
    snapshot = json.loads(analysis.chat_context_json) if analysis.chat_context_json else {}
    insights = await InsightGenerator.generate(report, snapshot)
    analysis.insights_json = json.dumps(insights)
    db.commit()
    return insights


@router.get("/report/{analysis_id}/pdf")
async def download_pdf_report(analysis_id: int, db: Session = Depends(get_db)):
    """Downloads the compiled ReportLab PDF report binary."""
    cached = db.query(models.RepositoryAnalysis).filter(
        models.RepositoryAnalysis.id == analysis_id
    ).first()
    
    if not cached:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
        
    try:
        # Re-generate PDF on the fly using the latest PDFGenerator and cached JSON data
        analysis_res = schemas.RepoAnalysisResponse.model_validate_json(cached.analysis_json)
        pdf_bytes = PDFGenerator.generate(analysis_res)
    except Exception as e:
        # Fallback to the saved blob if parsing or generation fails
        if cached.pdf_report:
            pdf_bytes = cached.pdf_report
        else:
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
        
    headers = {
        "Content-Disposition": f"attachment; filename=repo_audit_{cached.owner}_{cached.repo_name}.pdf"
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    """Lists recent audits from the cache database."""
    records = db.query(models.RepositoryAnalysis).order_by(
        models.RepositoryAnalysis.timestamp.desc()
    ).limit(30).all()
    
    return [
        {
            "id": r.id,
            "repo_url": r.repo_url,
            "owner": r.owner,
            "repo_name": r.repo_name,
            "score": r.score,
            "timestamp": r.timestamp,
            "scores": {
                "overall": r.score,
                "documentation": r.documentation_score,
                "security": r.security_score,
                "commits": r.commit_score,
                "structure": r.structure_score
            }
        } for r in records
    ]


@router.post("/compare")
async def compare_repositories(request: schemas.CompareRequest, db: Session = Depends(get_db)):
    """
    Accepts two repository URLs and returns both analyses side-by-side.
    """
    urls = request.urls
    if len(urls) != 2:
        raise HTTPException(status_code=400, detail="Comparison requires exactly two repository URLs")
        
    analyses = []
    for url in urls:
        # Re-use caching or run fresh scans
        cleaned_url = url.strip().lower()
        cutoff = datetime.utcnow() - timedelta(hours=settings.CACHE_EXPIRY_HOURS)
        cached = db.query(models.RepositoryAnalysis).filter(
            models.RepositoryAnalysis.repo_url == cleaned_url,
            models.RepositoryAnalysis.timestamp >= cutoff
        ).order_by(models.RepositoryAnalysis.timestamp.desc()).first()
        
        if cached:
            res_dict = json.loads(cached.analysis_json)
            res_dict["id"] = cached.id
            analyses.append(res_dict)
        else:
            try:
                analysis_res, chat_context = await run_full_analysis(url)
                
                try:
                    pdf_bytes = PDFGenerator.generate(analysis_res)
                except Exception:
                    pdf_bytes = None
                    
                db_entry = models.RepositoryAnalysis(
                    repo_url=cleaned_url,
                    owner=analysis_res.metadata.owner,
                    repo_name=analysis_res.metadata.name,
                    timestamp=analysis_res.timestamp,
                    score=analysis_res.scores.overall,
                    documentation_score=analysis_res.scores.documentation,
                    security_score=analysis_res.scores.security,
                    commit_score=analysis_res.scores.commits,
                    structure_score=analysis_res.scores.structure,
                    analysis_json=analysis_res.json(),
                    chat_context_json=json.dumps(chat_context),
                    pdf_report=pdf_bytes
                )
                db.add(db_entry)
                db.commit()
                db.refresh(db_entry)
                
                analysis_res.id = db_entry.id
                analyses.append(analysis_res.dict())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to scan repo {url}: {str(e)}")
                
    return {
        "repository_a": analyses[0],
        "repository_b": analyses[1]
    }
