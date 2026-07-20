from sqlalchemy import Column, Integer, String, Text, LargeBinary, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class RepositoryAnalysis(Base):
    __tablename__ = "repository_analyses"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String, index=True)
    owner = Column(String)
    repo_name = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer)
    documentation_score = Column(Integer)
    security_score = Column(Integer)
    commit_score = Column(Integer)
    structure_score = Column(Integer)
    analysis_json = Column(Text)  # JSON-encoded analysis summary
    chat_context_json = Column(Text, nullable=True)  # JSON-encoded repository context for chat
    insights_json = Column(Text, nullable=True)  # JSON-encoded cached repository insights
    pdf_report = Column(LargeBinary, nullable=True)  # Binary PDF contents


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("repository_analyses.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
