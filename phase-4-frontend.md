# Phase 4 — Frontend (Next.js)

## Ce qui a été fait

### 1. Structure du projet

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx          # Layout global + navbar
│   │   ├── page.tsx            # Landing page
│   │   ├── submit/page.tsx     # Formulaire client
│   │   ├── dashboard/
│   │   │   ├── page.tsx        # Vue ops (table + filtres + KPIs)
│   │   │   └── [claimId]/page.tsx  # Détail sinistre
│   │   └── analytics/page.tsx  # Métriques business
│   ├── components/
│   │   ├── RiskBadge.tsx       # Badge Low/Medium/High
│   │   ├── StatusBadge.tsx     # Badge de statut
│   │   └── MetricsCard.tsx     # Carte de métrique
│   └── lib/
│       └── api.ts              # Client API (16 fonctions)
├── package.json
├── next.config.js              # Proxy → FastAPI
├── tailwind.config.ts
└── tsconfig.json
```

### 2. Pages

| Page | Route | Description |
|---|---|---|
| Landing | `/` | Présentation + liens |
| Submit Claim | `/submit` | Formulaire de soumission |
| Dashboard | `/dashboard` | Vue ops: tableau + filtres + KPIs |
| Claim Detail | `/dashboard/[id]` | Détail complet + actions |
| Analytics | `/analytics` | Métriques business impact |

### 3. Claim Detail — Fonctionnalités

- Texte brut du client
- Extraction IA avec scores de confiance
- Champs manquantshighlightés
- Conversation agent ↔ client
- Score de risque + signaux
- Actions humaines : Approve / Reject / Escalate
- Simulateur de réponse client

### 4. Dashboard — Fonctionnalités

- KPIs en haut (Total, Submitted, Under Review, High Risk, Approved)
- Tableau des sinistres avec filtres (status, risk level)
- Navigation vers le détail au clic

### 5. API Proxy

Le frontend proxy les appels `/api/*` vers `localhost:8000` (FastAPI) via `next.config.js`.

## Pour lancer

```bash
cd "D:\projects\AI Insurance\frontend"
npm install
npm run dev
```

Frontend: http://localhost:3000
Backend: http://localhost:8000
API Docs: http://localhost:8000/docs
