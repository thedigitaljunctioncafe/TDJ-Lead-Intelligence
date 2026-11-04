# TDJ Lead Intelligence — Phase 1 Foundation

Local-first starter scaffold for Windows 11. This is a development foundation, not a finished lead scraper.

## Requirements
- Node.js 24+ and npm
- Python 3.11–3.13 recommended for broad package compatibility (your current Python 3.14.4 may work, but package compatibility must be tested)
- Git optional

## Folder layout
- `backend/` FastAPI API + SQLite persistence
- `frontend/` Next.js dashboard
- `data/` SQLite database is created automatically by the backend

## Start backend (PowerShell)
```powershell
cd .\backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
If dependency installation fails on Python 3.14, stop and share the error. Do not install another Python version yet.

Backend checks:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Start frontend (new PowerShell window)
```powershell
cd .\frontend
npm install
npm run dev
```
Open http://localhost:3000

## Phase 1 scope in this scaffold
- Dashboard shell
- Backend health endpoint
- Search job creation/listing
- SQLite persistence
- Local-first configuration

## Not implemented yet
- Authentication / user roles
- Web search adapters or scraping
- Ollama integration
- Lead extraction/scoring
- Excel export
- Remote/online access

These will be added only after the foundation is tested. Keep this app bound to localhost for now. Do not expose port 8000 or 3000 to the public internet.
