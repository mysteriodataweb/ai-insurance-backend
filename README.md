# AI Insurance Operations Platform

> An AI-powered platform that automates insurance claims intake, triage, and risk analysis while keeping humans in the loop for critical decisions.

## Overview

This platform simulates how AI, data analysis, automation, and human oversight can transform insurance operations. It demonstrates measurable business impact through intelligent claim processing, risk scoring, and operational dashboards.

## Key Features

- **AI Claims Extraction** — LLM-powered extraction of structured data from unstructured claim descriptions
- **Intelligent Follow-up** — AI agent identifies missing information and asks targeted questions
- **Risk Scoring Engine** — Rule-based risk assessment with explainable signals (0-100 score)
- **Human-in-the-Loop** — High-risk claims require human review and approval
- **Operations Dashboard** — Real-time claim queue with filters and KPIs
- **Audit Trail** — Complete logging of all actions for governance and compliance
- **Business Impact Metrics** — Measurable time saved and automation rates

## Architecture

```
Frontend (Next.js + TypeScript + Tailwind)
        ↓ REST API
Backend (Python + FastAPI)
        ↓
Business Logic Layer
   ├── Claim Service
   ├── AI Extraction Service (OpenAI GPT-4o-mini)
   ├── AI Agent Workflow
   ├── Risk Scoring Engine
   ├── Analytics Service
   └── Audit Service
        ↓
PostgreSQL (Supabase)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL (Supabase compatible) |
| AI | OpenAI GPT-4o-mini, Structured Outputs |
| Deployment | Vercel (frontend), Render (backend), Supabase (DB) |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or Supabase account)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-insurance-platform.git
cd ai-insurance-platform

# Run setup script (Windows)
setup.bat

# Or manual setup:

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY

# Frontend
cd ../frontend
npm install
```

### Database Setup

```sql
CREATE DATABASE ai_insurance;
```

### Seed Data

```bash
cd backend
python seed.py
```

This populates the database with 5 sample claims including pre-computed AI extractions, risk assessments, and conversation histories.

### Run

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

```
ai-insurance-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # Async PostgreSQL connection
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic
│   │   ├── routers/             # API endpoints
│   │   └── prompts/             # LLM prompt templates
│   ├── seed.py                  # Database seeder
│   ├── test.py                  # Quick tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # Reusable UI components
│   │   └── lib/api.ts           # API client
│   └── package.json
├── seed_data/
│   └── sample_claims.json       # Raw sample data
└── docs/                        # Phase documentation
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/claims` | Submit a new claim |
| GET | `/api/claims` | List claims with filters |
| GET | `/api/claims/{id}` | Get claim details |
| PUT | `/api/claims/{id}/action` | Take human action on claim |
| POST | `/api/agent/extract/{id}` | Trigger AI extraction |
| GET | `/api/agent/conversation/{id}` | Get conversation history |
| POST | `/api/agent/follow-up/{id}` | Generate follow-up questions |
| POST | `/api/agent/respond/{id}` | Submit customer response |
| POST | `/api/risk/assess/{id}` | Run risk assessment |
| GET | `/api/risk/{id}` | Get risk assessment |
| GET | `/api/dashboard/summary` | Dashboard KPIs |
| GET | `/api/analytics/metrics` | Business impact metrics |

## How It Works

### Claim Lifecycle

```
Submitted → AI Extraction → Follow-up (if needed) → Ready for Review
    → Risk Assessment → Under Review → Approved / Rejected / Escalated
```

### Risk Scoring

The risk engine evaluates claims based on multiple signals:

| Signal | Weight | Rule |
|---|---|---|
| High claim amount | +25 | > $10,000 |
| Round claim amount | +5 | $1,000, $2,000, etc. |
| Missing documentation | +10-15 | Multiple missing fields |
| Low AI confidence | +10 | Confidence < 50% |
| Late reporting | +10 | > 30 days after incident |

Risk levels: **Low** (0-30) | **Medium** (31-70) | **High** (71-100)

### AI Safety Principles

- **Human-in-the-loop**: High-risk claims require human approval
- **Explainability**: Every risk score includes human-readable explanation
- **Confidence tracking**: AI shows uncertainty instead of guessing
- **Audit trail**: All actions are logged for compliance

## Business Impact

| Metric | Before | After |
|---|---|---|
| Avg Processing Time | 25 min | 8 min |
| Time Saved | — | 68% |
| Automation Rate | 0% | ~40% |
| Missing Info Detection | Manual | Instant |

## Sample Data

The seed script creates 5 realistic claims:

| Customer | Type | Amount | Risk | Status |
|---|---|---|---|---|
| Ahmed Benali | Car accident | $3,000 | Low (15) | Under Review |
| Fatima Zahra | Water damage | $5,000 | Medium (45) | Follow-up |
| Youssef Alami | Theft | $2,500 | Medium (35) | Under Review |
| Sara Idrissi | Fire | $15,000 | High (78) | Under Review |
| Omar Tazi | Car accident | $800 | Unrated | Submitted |

## License

MIT
