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
│  │              OpenAI GPT-4o-mini                   │  │
│  │                                                   │  │
│  │  • Claim Information Extraction                   │  │
│  │  • Missing Field Detection                        │  │
│  │  • Follow-up Question Generation                  │  │
│  │  • Structured JSON Output                         │  │
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
│  ┌──────────┐ ┌──────────┐                             │
│  │  claim   │ │  audit   │                             │
│  │  actions │ │  logs    │                             │
│  └──────────┘ └──────────┘                             │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Claim Submission Flow

```
1. Customer submits form
   ↓
2. POST /api/claims → Claim stored (status: submitted)
   ↓
3. POST /api/agent/extract/{id}
   ↓
4. AI extracts structured data from raw description
   ↓
5. Missing fields detected?
   ├─ Yes → POST /api/agent/follow-up/{id}
   │        Agent generates questions
   │        Customer responds via POST /api/agent/respond/{id}
   │        Extraction updated
   │        Repeat until complete
   └─ No → Status: ready_for_review
   ↓
6. POST /api/risk/assess/{id}
   ↓
7. Risk scoring (0-100) with signals
   ↓
8. Status: under_review
   ↓
9. Human reviews and takes action
   ├─ Approve
   ├─ Reject
   └─ Escalate
```

## Database Schema

### Entity Relationship

```
claims (1) ──── (1) claim_extractions
claims (1) ──── (0..*) conversations
claims (1) ──── (1) risk_assessments
claims (1) ──── (0..*) claim_actions
claims (1) ──── (0..*) audit_logs
```

### Key Design Decisions

- **UUID primary keys** for security and distributed systems
- **JSONB columns** for flexible AI output storage
- **Enum types** for status and risk levels
- **Timestamps** on all tables for audit trail
- **Separate tables** for extractions, risks, and actions for clean data modeling
