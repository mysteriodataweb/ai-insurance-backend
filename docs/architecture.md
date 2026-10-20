# AI Insurance Operations Platform — Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                        │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Customer   │  │  Ops Agent  │  │  Ops Manager    │ │
│  │   Portal     │  │  Dashboard  │  │  Analytics      │ │
│  └──────┬───────┘  └──────┬──────┘  └────────┬────────┘ │
└─────────┼─────────────────┼──────────────────┼──────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                     │
│                                                         │
│              Next.js (TypeScript + Tailwind)            │
│                                                         │
│  • Submit Claim Page                                    │
│  • Operations Dashboard                                 │
│  • Claim Detail Page                                    │
│  • Analytics Page                                       │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   API LAYER                             │
│                                                         │
│                   FastAPI (Python)                      │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ /claims  │ │ /agent   │ │ /risk    │ │ /dashboard│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
└───────┼─────────────┼───────────┼──────────────┼────────┘
        │             │           │              │
        ▼             ▼           ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Claim      │  │     AI       │  │    Risk       │  │
│  │   Service     │  │   Extraction │  │    Engine     │  │
│  │              │  │   Service    │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │          │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  │
│  │    Audit      │  │     AI       │  │  Analytics   │  │
│  │   Service     │  │   Agent      │  │   Service    │  │
│  │              │  │   Workflow   │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    AI SERVICES                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Groq LLM (OpenAI-compatible API)             │  │
│  │                                                   │  │
│  │  • Claim Information Extraction                   │  │
│  │  • Customer Reply Understanding                   │  │
│  │  • Follow-up Question Generation                  │  │
│  │  • JSON output, validated before use              │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                           │
│                                                         │
│              PostgreSQL (Supabase)                      │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  claims   │ │  extrac- │ │  conver- │ │   risk    │  │
│  │          │ │  tions   │ │  sations │ │  assess-  │  │
│  │          │ │          │ │          │ │  ments    │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  claim   │ │  audit   │ │  claim   │ │   users   │  │
│  │  actions │ │  logs    │ │  attach- │ │           │  │
│  │          │ │          │ │  ments   │ │           │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Claim Submission Flow

```
1. Customer submits form (public)
   ↓
2. POST /api/claims → Claim stored (status: submitted)
   POST /api/claims/{id}/attachments → documents stored (optional)
   ↓
3. Background AI pipeline
   ├─ AI extraction (LLM) → validated, empty claim fields auto-filled
   ├─ Missing required fields computed in code
   ├─ Risk scoring (0-100, deterministic rules)
   └─ Missing fields? → follow-up questions (LLM, template fallback)
   ↓
4. Status: follow_up (waiting for the customer) or under_review
   ↓
5. Ops agent records the customer's reply → POST /api/agent/respond/{id}
   Extraction updated, status → ready_for_review when complete
   ↓
6. Human decision (authenticated) → PUT /api/claims/{id}/action
   ├─ Approve (high risk: escalation + second reviewer + justification)
   ├─ Reject (note required)
   ├─ Escalate
   └─ Request info
```

Every step writes to the audit trail (GET /api/claims/{id}/audit).

## Database Schema

### Entity Relationship

```
claims (1) ──── (1) claim_extractions
claims (1) ──── (0..*) conversations
claims (1) ──── (1) risk_assessments
claims (1) ──── (0..*) claim_actions
claims (1) ──── (0..*) audit_logs
claims (1) ──── (0..*) claim_attachments
users            (operations accounts, JWT auth)
```

### Key Design Decisions

- **UUID primary keys** for security and distributed systems
- **JSONB columns** for flexible AI output storage
- **Enum types** for status and risk levels
- **Timestamps** on all tables for audit trail
- **Separate tables** for extractions, risks, and actions for clean data modeling
