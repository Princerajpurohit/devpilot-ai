from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite needs check_same_thread=False for FastAPI concurrency
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema():
    """Apply the SQLite-compatible migration required for persisted chat context."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "repository_analyses" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("repository_analyses")}
    if "chat_context_json" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE repository_analyses ADD COLUMN chat_context_json TEXT"))
    if "insights_json" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE repository_analyses ADD COLUMN insights_json TEXT"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
