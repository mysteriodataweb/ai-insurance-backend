# AI Insurance Operations Platform — Backend

> FastAPI backend that triages insurance claims with an LLM, scores their risk with explainable rules, and keeps humans in charge of every decision.

The Next.js frontend lives in the separate `ai-insurance-frontend` repository.

## Key Features

- **Automatic AI triage** — every new claim is processed in the background: LLM extraction → risk scoring → follow-up questions when information is missing
- **AI Claims Extraction** — structured data and per-field confidence extracted from the free-text description, validated before use
- **Deterministic missing-field check** — required fields are checked in code, not by the LLM, so a crafted description can't skip the follow-up step
- **Explainable risk scoring** — rule-based score (0-100), each signal listed with its points
- **Human-in-the-loop workflow** — enforced status transitions; high-risk claims must be escalated and approved by a *second* person with a written justification (four-eyes rule)
- **Authentication** — JWT bearer tokens for every operations endpoint; only claim submission and document upload are public
- **Document upload** — PDF/PNG/JPEG/WEBP attachments, type checked from the file bytes, 5 MB each, 5 per claim
- **Audit trail** — every AI step and human decision is logged, readable through the API
- **Real operational metrics** — computed from the database, nothing simulated
- **Rate limiting** on public and AI endpoints

## Architecture

```
Frontend (Next.js) ──REST──▶ FastAPI
                               ├── Auth (JWT, PBKDF2 password hashing)
                               ├── Claim Service (workflow rules, four-eyes)
                               ├── AI Pipeline (background task)
                               │     ├── AI Extraction  ──▶ Groq (OpenAI-compatible API)
                               │     ├── Risk Engine (deterministic rules)
                               │     └── Follow-up Agent (LLM, template fallback)
                               ├── Attachment Service
                               ├── Analytics Service
                               └── Audit Service
                                       ▼
                               PostgreSQL (Supabase)
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.11, FastAPI, SQLAlchemy 2 (async), Pydantic 2 |
| Database | PostgreSQL (Supabase compatible) |
| AI | Groq API (`qwen/qwen3.8-27b` by default) via the OpenAI SDK, JSON mode |
| Auth | PyJWT (HS256), PBKDF2-SHA256 password hashing |
| Tests | pytest, pytest-asyncio, httpx |
| Deployment | Render (`render.yaml`) |

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (or a Supabase project)
- A Groq API key (free tier works)

### Installation

```bash
pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env: DATABASE_URL, GROQ_API_KEY, SECRET_KEY
```

On Windows, `setup.bat` does the same.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | local Postgres | `postgresql+asyncpg://...` connection string |
| `GROQ_API_KEY` | — | Without it, AI steps fail with HTTP 502 (the pipeline failure is logged in the audit trail) |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` | Any Groq chat model that supports JSON mode |
| `SECRET_KEY` | dev value | **Required in production** — the app refuses to start without it |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT lifetime |
| `ALLOW_REGISTRATION` | `true` | Set to `false` to close self-registration once your team has accounts |
| `CORS_ORIGINS` | localhost + Vercel URL | Comma-separated allowed browser origins |
| `AUTO_PROCESS_CLAIMS` | `true` | Run the AI pipeline automatically on submission |

### Database

Tables are created automatically at startup (missing tables only — existing data is never dropped or altered).

```bash
python seed.py           # adds 6 sample claims to an empty database
python seed.py --reset   # DROPS all tables, then seeds
```

### Run

```bash
uvicorn app.main:app --reload
```

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Tests

```bash
pytest                                   # unit tests
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_insurance_test pytest
                                         # + end-to-end API tests (the test database is wiped)
```

The LLM is faked in tests, so no API key is needed.

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create an operations account |
| POST | `/api/auth/login` | — | Get a bearer token |
| GET | `/api/auth/me` | ✔ | Current user |
| POST | `/api/claims` | — | Submit a claim (starts the AI pipeline) |
| POST | `/api/claims/{id}/attachments` | — | Upload documents (24 h after submission, or while in follow-up) |
| GET | `/api/claims` | ✔ | List claims (`status`, `risk_level`, `incident_type`, `limit`, `offset`) |
| GET | `/api/claims/{id}` | ✔ | Claim details |
| PUT | `/api/claims/{id}/action` | ✔ | Human decision: `approved`, `rejected`, `escalated`, `info_requested` |
| GET | `/api/claims/{id}/actions` | ✔ | Decision history |
| GET | `/api/claims/{id}/audit` | ✔ | Audit trail |
| GET | `/api/claims/{id}/attachments` | ✔ | List documents |
| GET | `/api/claims/{id}/attachments/{attachment_id}` | ✔ | Download a document |
| POST | `/api/agent/extract/{id}` | ✔ | (Re)run AI extraction |
| GET | `/api/agent/extraction/{id}` | ✔ | Latest extraction |
| GET | `/api/agent/conversation/{id}` | ✔ | Conversation history |
| POST | `/api/agent/follow-up/{id}` | ✔ | Generate follow-up questions |
| POST | `/api/agent/respond/{id}` | ✔ | Record the customer's reply and update the claim |
| POST | `/api/risk/assess/{id}` | ✔ | (Re)run risk assessment |
| GET | `/api/risk/{id}` | ✔ | Risk assessment |
| GET | `/api/dashboard/summary` | ✔ | Dashboard KPIs |
| GET | `/api/analytics/metrics` | ✔ | Operational metrics |

Errors: `404` unknown resource, `409` action not allowed in the claim's current state, `422` invalid input, `429` rate limited, `502` AI provider failure.

## How It Works

### Claim Lifecycle

```
submitted ──AI extraction──▶ follow_up (fields missing) ──customer reply──▶ ready_for_review
                         └─▶ ready_for_review ──risk assessment──▶ under_review
under_review ──▶ approved | rejected | escalated | follow_up (info requested)
escalated    ──▶ approved (second reviewer) | rejected | follow_up
```

Approved and rejected claims are closed: AI steps and new decisions are refused.

### Decision Rules

| Rule | Enforced by |
|---|---|
| A claim can only be approved after a risk assessment | `PUT /action` → 409 |
| Rejections need a note | `PUT /action` → 409 |
| High-risk claims must be escalated before approval | `PUT /action` → 409 |
| High-risk approval needs a written justification | `PUT /action` → 409 |
| The approver of a high-risk claim must differ from the person who escalated it | `PUT /action` → 409 |

### Risk Scoring

| Signal | Points |
|---|---|
| Claim amount > $10,000 / > $25,000 | +30 / +45 |
| Round amount (multiple of $1,000) | +5 |
| Declared amount differs > 20% from the amount in the description | +20 |
| One / several required fields missing | +10 / +20 |
| AI extracted a field with confidence < 50% | +10 |
| Reported > 30 / > 90 days after the incident | +15 / +25 |
| Incident date in the future | +20 |
| Same customer filed 1 / 2+ other claims in 12 months | +5 / +15 |

Risk levels: **Low** (0-30) | **Medium** (31-70) | **High** (71-100), capped at 100.

### AI Safety Principles

- **Customer text is untrusted**: it is passed to the LLM inside delimiters, with instructions to treat it as data
- **LLM output is validated**: every field is type-checked and coerced; unusable values become null, confidences are clamped to 0-1
- **The LLM doesn't decide alone**: missing fields and risk are computed by deterministic code; the declared vs. described amount cross-check catches inconsistencies
- **Human-in-the-loop**: every decision is human, high-risk ones need two people
- **Audit trail**: every step is logged with its actor

### Metrics

`/api/analytics/metrics` reports real figures: AI-processed rate, share of assessed claims needing human review, low-risk claims eligible for fast-track, average time to AI triage, average time to decision, claims per day/week, by type and by risk. There are no "before/after" productivity numbers: those would need a real baseline measurement.

## Sample Data

`seed.py` creates 6 claims; scores come from the real risk engine:

| Customer | Type | Amount | Risk | Status |
|---|---|---|---|---|
| Ahmed Benali | Car accident | $3,000 | Low (5) | Approved |
| Fatima Zahra | Water damage | $5,000 | Low (15) | Follow-up (policy number missing) |
| Youssef Alami | Theft | $2,500 | Low (0) | Under review |
| Sara Idrissi | Fire | $15,000 | Medium (35) | Escalated |
| Karim Mansouri | Theft | $30,000 declared, $18,000 described | High (100) | Under review |
| Omar Tazi | Car accident | $800 | Unrated | Submitted (not processed yet) |

## Known Limitations

- No schema migrations: new tables are created at startup, but changing an existing column needs a manual SQL migration (Alembic is not set up).
- Rate limiting is in memory, per process: fine for one instance, not for several.
- The AI pipeline runs as a FastAPI background task in the API process; there is no job queue or automatic retry.
- Attachments are stored in PostgreSQL (fine for a demo, not for large volumes) and are not analyzed by the AI.
- Customer descriptions are sent to a third-party AI provider (Groq); a real deployment needs customer consent and a data processing agreement (GDPR / Moroccan law 09-08).
- Any registered user can act on any claim; there are no role-based permissions beyond the four-eyes rule.

## License

MIT
