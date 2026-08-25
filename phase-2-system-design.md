# Phase 2 — System Design

## 1. Architecture technique

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                │
│  Customer Form  │  Ops Dashboard  │  Analytics      │
└────────────────────────┬────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────┐
│                 BACKEND (FastAPI)                    │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │  Claim   │ │   AI     │ │  Risk Scoring    │    │
│  │ Service  │ │ Service  │ │  Engine          │    │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘    │
│       │            │                │               │
│  ┌────▼────────────▼────────────────▼─────────┐     │
│  │           Business Logic Layer              │     │
│  └────────────────────┬───────────────────────┘     │
│                       │                             │
│  ┌──────────┐ ┌───────▼──────┐ ┌────────────────┐  │
│  │  Audit   │ │  Analytics   │ │  Agent         │  │
│  │ Service  │ │  Service     │ │  Workflow      │  │
│  └──────────┘ └──────────────┘ └────────────────┘  │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              PostgreSQL (Supabase)                   │
│  claims │ extractions │ conversations │ audit_logs   │
└─────────────────────────────────────────────────────┘
```

## 2. Structure des dossiers

```
D:\projects\AI Insurance\
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── claim.py
│   │   │   ├── extraction.py
│   │   │   ├── conversation.py
│   │   │   ├── risk_assessment.py
│   │   │   └── audit_log.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── claim.py
│   │   │   ├── extraction.py
│   │   │   ├── conversation.py
│   │   │   ├── risk.py
│   │   │   └── audit.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── claim_service.py
│   │   │   ├── ai_extraction.py
│   │   │   ├── ai_agent.py
│   │   │   ├── risk_engine.py
│   │   │   ├── analytics_service.py
│   │   │   └── audit_service.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── claims.py
│   │   │   ├── agent.py
│   │   │   ├── dashboard.py
│   │   │   └── analytics.py
│   │   └── prompts/
│   │       ├── extraction.py
│   │       └── follow_up.py
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── submit/page.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [claimId]/page.tsx
│   │   │   └── analytics/page.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── ClaimForm.tsx
│   │   │   ├── ClaimTable.tsx
│   │   │   ├── ClaimDetail.tsx
│   │   │   ├── RiskBadge.tsx
│   │   │   ├── MetricsCard.tsx
│   │   │   └── AuditTimeline.tsx
│   │   └── lib/api.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.js
│
├── docs/
│   ├── phase-1-product-definition.md
│   ├── phase-2-system-design.md
│   └── architecture.md
│
└── seed_data/
    └── sample_claims.json
```

## 3. Schéma de la base de données

### Table `claims`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | Identifiant unique |
| policy_number | VARCHAR | Numéro de police (peut être null) |
| customer_name | VARCHAR | Nom du client |
| customer_email | VARCHAR | Email du client |
| raw_description | TEXT | Texte brut soumis par le client |
| incident_type | VARCHAR | Type d'incident |
| incident_date | DATE | Date de l'incident |
| incident_location | VARCHAR | Lieu de l'incident |
| estimated_amount | DECIMAL | Montant estimé |
| status | ENUM | submitted → extracting → follow_up → ready_for_review → under_review → approved / rejected / escalated |
| risk_level | ENUM | unrated / low / medium / high |
| created_at | TIMESTAMP | Création |
| updated_at | TIMESTAMP | Dernière mise à jour |

### Table `claim_extractions`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | |
| claim_id | UUID (FK → claims) | |
| extracted_data | JSONB | Données structurées extraites par l'IA |
| missing_fields | JSONB | Liste des champs manquants |
| confidence_scores | JSONB | Score de confiance par champ |
| extraction_raw | JSONB | Réponse brute du LLM |
| created_at | TIMESTAMP | |

### Table `conversations`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | |
| claim_id | UUID (FK → claims) | |
| role | ENUM | agent / customer |
| message | TEXT | Message |
| message_type | ENUM | question / answer / info_request / system |
| created_at | TIMESTAMP | |

### Table `risk_assessments`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | |
| claim_id | UUID (FK → claims) | |
| risk_score | INTEGER | 0-100 |
| risk_level | ENUM | low / medium / high |
| signals | JSONB | Liste des signaux détectés |
| explanation | TEXT | Explication lisible |
| recommended_action | TEXT | Action recommandée |
| created_at | TIMESTAMP | |

### Table `claim_actions`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | |
| claim_id | UUID (FK → claims) | |
| action | ENUM | approved / rejected / escalated / info_requested |
| performed_by | VARCHAR | Qui a fait l'action |
| notes | TEXT | Commentaires |
| created_at | TIMESTAMP | |

### Table `audit_logs`

| Colonne | Type | Description |
|---|---|---|
| id | UUID (PK) | |
| claim_id | UUID (FK → claims) | |
| event_type | VARCHAR | Type d'événement |
| event_data | JSONB | Détails de l'événement |
| actor | VARCHAR | system / ai_agent / ops_agent |
| created_at | TIMESTAMP | |

## 4. API Endpoints

### Claims

| Méthode | Endpoint | Description |
|---|---|---|
| POST | /api/claims | Soumettre un sinistre |
| GET | /api/claims | Lister les sinistres (filtres) |
| GET | /api/claims/{id} | Détail d'un sinistre |
| PUT | /api/claims/{id}/action | Action humaine |

### AI Agent

| Méthode | Endpoint | Description |
|---|---|---|
| POST | /api/agent/extract/{claim_id} | Déclencher extraction IA |
| GET | /api/agent/conversation/{claim_id} | Historique conversation |
| POST | /api/agent/respond/{claim_id} | Répondre aux questions |

### Risk

| Méthode | Endpoint | Description |
|---|---|---|
| POST | /api/risk/assess/{claim_id} | Évaluer le risque |
| GET | /api/risk/{claim_id} | Résultat de l'évaluation |

### Dashboard & Analytics

| Méthode | Endpoint | Description |
|---|---|---|
| GET | /api/dashboard/summary | KPIs globaux |
| GET | /api/dashboard/claims | Vue table avec filtres |
| GET | /api/analytics/metrics | Métriques business |
| GET | /api/analytics/trends | Tendances |

## 5. Claim Lifecycle

```
submitted ──────────────────► extracting
   │                              │
   │                     (LLM extraction done)
   │                              │
   │                              ▼
   │                         follow_up
   │                              │
   │                     (all fields complete)
   │                              │
   │                              ▼
   │                       ready_for_review
   │                              │
   │                     (risk assessment done)
   │                              │
   │                              ▼
   │                        under_review
   │                              │
   │               ┌──────────────┼──────────────┐
   │               ▼              ▼              ▼
   │          approved       rejected       escalated
   │
   └─── (customer can submit at any time)
```

## 6. AI Agent Workflow

```
1. Claim reçu (status: submitted)
2. Déclencher extraction IA (status → extracting)
   - LLM analyse le texte brut
   - Extrait les champs structurés
   - Identifie les champs manquants
   - Évalue la confiance par champ
3. Champs manquants détectés ? (status → follow_up)
   Oui → Agent pose des questions ciblées
        → Client répond
        → Extraction mise à jour
        → Répéter jusqu'à complétude
   Non → Passe à l'analyse de risque (status → ready_for_review)
4. Risk scoring (status → under_review)
   - Règles + signaux
   - Score 0-100
   - Classification Low/Medium/High
5. Routing selon le risque
   - Low → Traitement rapide
   - Medium → Revue humaine recommandée
   - High → Revue humaine obligatoire
6. Décision humaine (approved / rejected / escalated)
```

## 7. Risk Scoring — Signaux

| Signal | Poids | Règle |
|---|---|---|
| Montant anormalement élevé | +25 | > 2x la moyenne historique |
| Sinistres multiples récents | +20 | > 3 sinistres en 30 jours |
| Informations incohérentes | +15 | Contradictions détectées par l'IA |
| Documents manquants | +10 | Pas de preuve jointe |
| Lieu inhabituel | +10 | Hors zone habituelle du client |
| Timing suspect | +10 | Déclaration tardive > 48h |
| Montant rond | +5 | 1000, 2000, 5000... |
