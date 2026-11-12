# TDJ Lead Intelligence

**The Digital Junction | Local-first Lead Discovery & Intelligence Platform**

## Purpose
Discover potential business leads and publicly expressed customer service requirements from lawful, publicly accessible online sources. The platform is not limited to Google Maps, restaurants, or one business category.

## Discovery scope

### Business discovery
- New retail shops and commercial establishments
- Restaurants, cafes and food businesses
- Factories and manufacturing units
- Clinics and healthcare establishments
- Wholesalers and distributors
- Real estate promoters and builders
- New housing and apartment projects

### Customer service intent
- Aadhaar, PAN, voter and ration services
- Passport and caste certificates
- Trade licence and driving licence
- GST registration and filing
- Income tax returns
- Khajna, mutation and porcha
- Website and software development
- Online form filling
- Rail, air and bus ticket booking
- Printing and scanning

Business discovery signals, potential opportunities and confirmed customer intent must remain separate. A newly discovered business must never automatically be represented as a customer who has requested a service.

## Current architecture

**Backend:** Python, FastAPI, SQLAlchemy, SQLite, Alembic migrations, server-side authentication and sessions, workspace-based access isolation, business discovery and service-intent matching, intelligence persistence, controlled connector framework, domain allowlist and pinned HTTPS transport.

**Frontend:** Next.js 16, React 19 and TypeScript. The existing frontend is a starting dashboard, not a completed product.

**Local AI:** Ollama is the intended local AI runtime. Qwen3:8B is the initial preferred local model for experimentation. No mandatory paid AI API. AI Studio is a development environment, not the production AI runtime.

## Database and migration policy
- SQLite database is maintained locally.
- Alembic is the authoritative schema migration system.
- Never use automatic schema creation as a replacement for migrations.
- Never reset, drop, overwrite or recreate the existing database.
- Never downgrade migrations without explicit approval.
- Back up the database before any approved migration.
- Preserve existing users, workspace memberships, leads and records.
- The handoff copy intentionally does not contain the actual database.

## Local development

Backend, from the project root:
```powershell
cd .\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in another PowerShell window:
```powershell
cd .\frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:3000
- Backend health: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs

The handoff copy does not include an installed virtual environment. Use the actual local Python environment and dependency configuration.

## Testing

Backend regression suite:
```powershell
cd .\backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The source project passed 374 tests on 6 November 2026. This is a historical baseline, not a guarantee that future changes pass.

Frontend validation:
```powershell
cd .\frontend
npm run lint
npm run build
```

## Security principles
- Keep the application local during development.
- Do not expose local development ports publicly.
- Enforce authentication and workspace authorization.
- Keep secrets in environment variables, never source control.
- Never bypass connector domain allowlists or pinned HTTPS transport.
- Reject private, loopback and internal network destinations.
- Do not bypass logins, CAPTCHAs, access controls or private areas.
- Respect source terms, robots policies, rate limits and applicable privacy laws.

## Cost and deployment
- Target operating cost: ₹0 wherever possible.
- Absolute recurring budget ceiling: ₹100/month unless explicitly revised.
- Prefer free and open-source components.
- Local Ollama is preferred for AI inference.
- Do not introduce paid APIs, subscriptions or cloud dependencies without approval.
- Local deployment comes first. Online deployment requires a separate security review.

## Development strategy
Google AI Studio Build mode is a development assistant for frontend development, feature implementation and code review. The existing Python FastAPI backend remains authoritative. Do not rewrite the backend as Node.js or replace the database architecture.

Every proposed change must be reviewed, copied into the local development environment, tested and verified before acceptance. No automatic production deployment, Git commit or Git push is authorized.
