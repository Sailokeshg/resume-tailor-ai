# Copilot Instructions for resume-tailor-ai

## Project Overview

- **Purpose:** AI-powered web app to tailor resumes for specific job descriptions using Retrieval-Augmented Generation (RAG) and vector databases.
- **Architecture:**
  - **Frontend:** React (Vite, Tailwind CSS), in `frontend/`
  - **Backend:** Python FastAPI (not Node.js/Express as README says), in `backend/`
  - **AI Integration:** Backend connects to OpenAI API and vector DB for RAG.
  - **Docker:** Use `docker-compose.yml` for full-stack orchestration.

## Key Workflows

- **Frontend:**
  - Install: `cd frontend && npm install`
  - Dev server: `npm run dev` (Vite, not `npm start`)
  - Main entry: `src/App.jsx`, UI logic in `src/components/`, API calls in `src/services/api.js`
- **Backend:**
  - Install: `cd backend && pip install -r requirements.txt`
  - Run: `uvicorn main:app --reload`
  - API routes: `backend/app/api/v1/endpoints/`
  - AI logic: `backend/app/services/ai_service.py`, RAG in `rag_service.py`, vector DB in `vector_service.py`
- **Environment:**
  - Backend: Copy `.env.example` to `.env` and set OpenAI key
  - Frontend: No .env required unless using custom API URLs
- **Docker:**
  - `docker-compose up --build` to run both services

## Patterns & Conventions

- **API Versioning:** All backend endpoints under `/api/v1/`
- **Separation:**
  - `models/` = Pydantic models
  - `schemas/` = request/response schemas
  - `services/` = business logic, AI, vector DB
  - `utils/` = helpers (file, latex)
- **Frontend:**
  - Use hooks in `src/hooks/` for API/data logic
  - UI components in `src/components/`
  - Tailwind for all styling
- **Testing:**
  - No explicit test suite found; add tests in `backend/tests/` or `frontend/src/__tests__/` if needed

## Integration Points

- **Frontend <-> Backend:**
  - API calls via `/api/v1/` endpoints
  - File upload and text input supported
- **Backend <-> OpenAI/Vector DB:**
  - See `ai_service.py`, `rag_service.py`, `vector_service.py`

## Examples

- Add a new API endpoint: `backend/app/api/v1/endpoints/`
- Add a new UI feature: `frontend/src/components/` and update `App.jsx`

## References

- See `README.md` in root, `frontend/`, and `backend/` for more details.

---

_Update this file if you add new workflows, conventions, or major features._
