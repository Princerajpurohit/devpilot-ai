# DevPilot AI — Understand. Debug. Document. Improve.

DevPilot AI is a full-stack, production-ready GitHub repository evaluation platform. It analyzes any public GitHub repository to generate technical insights, code quality reviews, commit analytics, hygiene checklists, OSV dependency security scans, and a downloadable PDF report.

---

## Technical Stack

- **Frontend:** Next.js (TypeScript, Tailwind CSS, Framer Motion, Recharts, Lucide Icons)
- **Backend:** Python (FastAPI, HTTPX, SQLAlchemy, SQLite, ReportLab, Google Generative AI SDK)
- **Deployment:** Docker & Docker Compose

---

## Features

- **Circular Score Meter (0-100):** Weighted by Security (30%), Documentation (30%), Commit Quality (20%), and Structure (20%).
- **Documentation Analyzer:** Audits README structures for descriptors, installations, examples, demos, and licensing.
- **Commit History Analyzer:** Compiles timelines, unique contributors count, and flags lazy messages (e.g. "fix", "wip").
- **Security Audit Scanner:** Regex searches codebase scripts for leaked secrets and queries the Google OSV API database for dependency vulnerabilities.
- **Actionable Fix-It Roadmap:** Ranks issues by score gain impact, providing estimate difficulty, time, and resolution advice.
- **ReportLab PDF Downloads:** Generates corporate-grade multi-page vector PDF documents summarizing findings.
- **Compare Mode:** Visualizes side-by-side metric audits for two competitor codebases.
- **SQLite caching:** Prevents rate-limit exhaustion and stores binary report PDFs.

---

## Getting Started

### Prerequisites

Ensure you have [Python 3.10+](https://www.python.org/downloads/) and [Node.js 18+](https://nodejs.org/) installed locally.

### 1. Launching the Backend API
1. Navigate to the `/backend` folder:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your environment keys (Optional - create a `.env` file):
   ```env
   GITHUB_TOKEN=your_github_token
   GEMINI_API_KEY=your_gemini_api_key
   ```
4. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend will boot at `http://localhost:8000`. Swagger docs are available at `/docs`.*

### 2. Launching the Next.js Frontend
1. Navigate to the `/frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Install Node modules:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Run the development build:
   ```bash
   npm run dev
   ```
   *Open `http://localhost:3000` to interact with DevPilot AI.*

---

## Running with Docker Compose

To start the complete stack in a containerized environment, simply run the following command from the root directory:

```bash
docker-compose up --build
```

The stack will start:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
