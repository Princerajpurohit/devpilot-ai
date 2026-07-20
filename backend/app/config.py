import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./repo_intelligence.db")
    CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

settings = Settings()
