# TDJ Lead Intelligence — AI Studio Master Instructions

You are working on **TDJ Lead Intelligence**, a project owned by The Digital Junction. Assist with development while preserving the existing architecture, data, security controls and business requirements. These instructions are mandatory.

## 1. Non-negotiable architecture

The existing backend is Python FastAPI. The database is SQLite, managed through SQLAlchemy and Alembic. The frontend is Next.js, React and TypeScript. The intended AI runtime is local Ollama.

Google AI Studio is a development assistant. It is NOT authorized to replace the production architecture.

Never:
- Rewrite the Python backend in Node.js.
- Replace FastAPI with another backend framework.
- Replace SQLite with Firebase, Supabase, MongoDB or another database.
- Replace Alembic with automatic schema creation.
- Remove existing authentication or workspace isolation.
- Replace local Ollama with a mandatory paid AI API.
- Rebuild the project from scratch when an incremental change is possible.

You may improve the Next.js frontend and its components. Backend changes must be limited to the explicitly requested task and preserve existing contracts.

## 2. Protect existing data

The original local database is not part of this handoff copy.

Never reset or drop the database, delete existing tables or records, overwrite existing user/workspace data, run destructive SQL, downgrade migrations, or change migration history to conceal a schema problem.

Before proposing any schema change:
1. Explain why it is necessary.
2. Identify affected tables, columns, indexes and relationships.
3. Explain backward compatibility.
4. Provide a safe migration plan.
5. Explain the backup and rollback strategy.
6. Wait for explicit authorization before applying a potentially destructive change.

Alembic remains the sole authoritative migration mechanism.

## 3. Authentication and authorization

Preserve server-side session authentication, secure password hashing, HttpOnly session cookies, user activation checks, workspace membership validation, role-based permissions, cross-workspace data isolation and admin-only operations.

Never trust a workspace ID, user ID, role or permission supplied by the frontend without server-side validation. Never expose sensitive information through API responses, logs or browser storage.

## 4. Connector and network security

The existing connector framework uses controlled execution, workspace-approved domains, URL validation and pinned HTTPS transport. Every new public-source connector must respect this architecture.

Never:
- Add unrestricted HTTP fetching.
- Bypass the approved-domain system.
- Follow redirects without revalidating the destination.
- Allow requests to localhost, private IPs, internal services or cloud metadata endpoints.
- Trust arbitrary user-provided URLs.
- Disable DNS/IP validation.
- Bypass rate limits or response-size limits.
- Add a connector that independently opens unrestricted network connections.

Use the existing controlled transport contract. Do not bypass login systems, CAPTCHAs, paywalls, access controls, robots restrictions or private groups.

Collect only lawfully accessible public information. Respect terms of service, applicable privacy/data protection laws, source attribution and reasonable rate limits. Do not promise unlimited crawling or unrestricted scraping.

## 5. Product requirements

The platform must support multiple categories of lead discovery.

**Business discovery:** new shops and retail businesses; restaurants and cafes; factories and manufacturers; clinics and healthcare businesses; wholesalers and distributors; real estate promoters and builders; housing and apartment projects.

**Customer service intent:** discover public posts and pages where people explicitly express a need for services offered by The Digital Junction, such as PAN, Aadhaar, passport, voter, GST, website/software development, online form filling and other listed services.

Keep these categories separate:
1. **Discovery signal:** A business or relevant entity was discovered.
2. **Potential opportunity:** A business may need a service, but has not confirmed demand.
3. **Confirmed service intent:** A public source explicitly expresses a service requirement.

Never convert a potential opportunity into confirmed customer intent without evidence. A low review count, new-looking website or missing online history is not sufficient proof that a business is newly established.

## 6. Local AI and cost

- Ollama is the preferred AI runtime.
- Keep inference local.
- Do not require Gemini API, OpenAI API or another paid AI service for normal operation.
- Do not transmit private customer data to external AI services.
- Do not add paid services or recurring infrastructure without explicit approval.
- Target ₹0 recurring cost, with a strict ceiling of ₹100/month unless the owner changes it.

AI Studio may assist in writing code. Its own AI capabilities must not become a mandatory runtime dependency.

## 7. Frontend development

You may improve dashboard layout, navigation, responsive design, lead tables/detail views, search/filter interfaces, analytics, forms, validation, loading/empty/error states, accessibility and usability.

Use the existing Next.js, React and TypeScript stack. Do not create mock frontend data that is presented as real persisted leads. Clearly distinguish demo data from actual backend data. Do not expose secrets or privileged backend logic in client-side code.

## 8. Backend development

Before changing backend code:
1. Inspect the existing implementation.
2. Identify the existing API contract.
3. Reuse existing services and models where possible.
4. Avoid duplicated business logic.
5. Preserve workspace boundaries.
6. Add regression tests.
7. Explain any migration impact.

Never silently change API response shapes or authentication behavior. Do not introduce a new backend architecture for convenience.

## 9. Testing requirements

The source project passed 374 backend regression tests on 6 November 2026. Treat this as the baseline.

For every meaningful change:
- Add or update relevant tests.
- Run the relevant test suite.
- Run the full backend regression suite when backend code changes.
- Run frontend lint and production build when frontend code changes.
- Report actual test results.
- Identify failures and warnings honestly.

Never claim tests passed if they were not executed. Never delete, skip or weaken an existing test merely to make a build pass.

## 10. Environment and secrets

Never ask the owner to upload real `.env` files, passwords, session tokens, API keys, private database files or production credentials. Use `.env.example` for configuration documentation. Never hardcode credentials in source code.

## 11. Git and deployment

No Git commit, push, merge, release or deployment is authorized automatically. Never push to master. Never deploy publicly without explicit approval. Keep all development changes reviewable and reversible.

## 12. Required workflow for every task

Before making changes:
1. Restate the requested task.
2. Inspect relevant files.
3. Explain the proposed implementation.
4. Identify risks and affected components.
5. Identify whether a database migration is required.

After making changes:
1. List every changed file.
2. Explain each change.
3. List tests executed and their actual results.
4. Report security implications.
5. Report migration implications.
6. Identify any incomplete work.
7. Provide exact local verification instructions.

If the requested change conflicts with these instructions, stop and explain the conflict. Do not silently choose a destructive workaround.

## 13. First task — read-only project audit

When this project is first loaded, do not immediately modify files.

First inspect:
- Complete project structure.
- Backend entry point and route registration.
- Models and relationships.
- Alembic migration history.
- Authentication and authorization.
- Connector security and workspace transport.
- Intelligence matching and persistence.
- Frontend architecture and existing UI.
- Existing tests and dependency configuration.

Produce a structured audit with:
1. Existing architecture.
2. Implemented features.
3. Incomplete features.
4. Security gaps.
5. Frontend/backend integration gaps.
6. Recommended next development priorities.
7. Risks and dependencies.

Do not change the database, migrations, authentication, connector security or backend architecture during this first audit.

Wait for the owner's approval before implementing the next feature.

---

**Owner priority:** Preserve existing work, protect customer data, maintain local-first operation, minimize recurring costs and make every change testable and reversible.
