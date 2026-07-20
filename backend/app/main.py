from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.database import engine, Base, ensure_schema

# Create SQLite database tables on startup
Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(
    title="GitHub Repository Intelligence API",
    description="Full-stack repository analyzer yielding documentation grades, security vulnerability CVE scans, and git commit history reviews.",
    version="1.0.0"
)

# Configure CORS for Local Development and Sandbox testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits Next.js dev server or local HTML files
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "GitHub Repository Intelligence Engine",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
