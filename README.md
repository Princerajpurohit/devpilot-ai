# DevPilot AI

An AI Software Engineer that understands your GitHub repository — explains code, chats about it, generates documentation, and finds issues.

## Built for OpenAI Build Week Hackathon

## What it does
- **GitHub Repository Import** — import any repo and get an instant structural overview
- **AI Chat with Repository** — ask questions about the codebase and get accurate, context-aware answers
- **Documentation Generator** — automatically generates README and documentation based on actual code
- **Insights** — highlights issues, risks, and improvement areas in the codebase

## Tech Stack
- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: SQLite
- AI: Gemini API

## How Codex & GPT-5.6 were used
This entire project was built using Codex and GPT-5.6 in a phased development approach:
- Phase 1: Planning and architecture setup
- Phase 2: Repository import and parsing logic
- Phase 3: AI chat feature and documentation generator
- Phase 4: Insights engine and UI polish

Codex was used to write and structure a large portion of both the backend (FastAPI endpoints, repo parsing, analysis logic) and frontend (Next.js pages, components) code. GPT-5.6 powered the core reasoning behind the AI chat and documentation generation features.

## Setup Instructions
1. Clone the repository
2. Backend: `cd backend`, `pip install -r requirements.txt`, run the FastAPI server
3. Frontend: `cd frontend`, `npm install`, `npm run dev`
4. Open localhost in your browser to access DevPilot AI