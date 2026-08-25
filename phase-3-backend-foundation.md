# Phase 3 — Backend Foundation

## Ce qui a été fait

### 1. Structure du projet FastAPI

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Variables d'environnement
│   ├── database.py          # Connexion async PostgreSQL
│   ├── models/              # SQLAlchemy ORM
│   │   ├── claim.py
│   │   ├── extraction.py
│   │   ├── conversation.py
│   │   ├── risk_assessment.py
│   │   └── audit_log.py
│   ├── schemas/             # Pydantic (validation)
│   │   ├── claim.py
│   │   ├── extraction.py
│   │   ├── conversation.py
│   │   ├── risk.py
│   │   └── audit.py
│   ├── services/            # Logique métier
│   │   ├── claim_service.py
│   │   ├── ai_extraction.py
│   │   ├── ai_agent.py
│   │   ├── risk_engine.py
│   │   ├── analytics_service.py
│   │   └── audit_service.py
│   ├── routers/             # Endpoints API
│   │   ├── claims.py
│   │   ├── agent.py
│   │   ├── dashboard.py
│   │   └── risk.py
│   └── prompts/
├── requirements.txt
├── .env.example
```

### 2. Base de données (6 tables)

| Table | Description |
|---|---|
| `claims` | Sinistres principaux |
| `claim_extractions` | Données extraites par l'IA |
| `conversations` | Messages agent ↔ client |
| `risk_assessments` | Évaluations de risque |
| `claim_actions` | Décisions humaines |
| `audit_logs` | Trail d'audit complet |

### 3. Services créés

| Service | Rôle |
|---|---|
| `claim_service` | CRUD sinistres, filtres, stats |
| `ai_extraction` | Extraction structurée via LLM |
| `ai_agent` | Workflow extraction → follow-up |
| `risk_engine` | Scoring de risque par règles |
| `analytics_service` | Métriques business |
| `audit_service` | Enregistrement des événements |

### 4. Endpoints API

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/claims` | Soumettre un sinistre |
| GET | `/api/claims` | Lister avec filtres |
| GET | `/api/claims/{id}` | Détail |
| PUT | `/api/claims/{id}/action` | Action humaine |
| POST | `/api/agent/extract/{id}` | Extraction IA |
| GET | `/api/agent/conversation/{id}` | Historique |
| POST | `/api/agent/follow-up/{id}` | Questions de suivi |
| POST | `/api/agent/respond/{id}` | Réponse client |
| POST | `/api/risk/assess/{id}` | Évaluation risque |
| GET | `/api/risk/{id}` | Résultat risque |
| GET | `/api/dashboard/summary` | KPIs |
| GET | `/api/analytics/metrics` | Métriques business |

### 5. Données de test

`seed_data/sample_claims.json` — 5 sinistres variés (accident, vol, incendie, dégât des eaux)

## Pour lancer

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configurer DATABASE_URL et OPENAI_API_KEY
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
