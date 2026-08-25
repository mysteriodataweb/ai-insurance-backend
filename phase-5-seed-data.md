# Phase 5 — Seed Data + Démonstration

## Ce qui a été fait

### 1. Script de seed (`backend/seed.py`)

Peuple la base avec **5 sinistres variés** pré-calculés :

| # | Client | Type | Montant | Statut | Risque |
|---|---|---|---|---|---|
| 1 | Ahmed Benali | Car accident | $3,000 | Under Review | Low (15) |
| 2 | Fatima Zahra | Water damage | $5,000 | Follow-up | Medium (45) |
| 3 | Youssef Alami | Theft | $2,500 | Under Review | Medium (35) |
| 4 | Sara Idrissi | Fire | $15,000 | Under Review | High (78) |
| 5 | Omar Tazi | Car accident | $800 | Submitted | Unrated |

Chaque sinistre inclut :
- Extraction IA pré-calculée avec scores de confiance
- Score de risque + signaux expliqués
- Conversations agent ↔ client
- Actions humaines
- Audit trail complet

### 2. Script de test (`backend/test.py`)

Vérifie que le risk engine fonctionne sur les données de seed.

### 3. Script de setup (`setup.bat`)

Installe automatiquement les dépendances backend + frontend et guide l'utilisateur.

## Pour lancer

```bash
# 1. Créer la base PostgreSQL
CREATE DATABASE ai_insurance;

# 2. Configurer backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_insurance
OPENAI_API_KEY=sk-...

# 3. Peupler la base
cd backend
python seed.py

# 4. Lancer le backend
uvicorn app.main:app --reload

# 5. Lancer le frontend
cd ../frontend
npm run dev

# 6. Ouvrir http://localhost:3000
```

Ou utiliser `setup.bat` pour tout installer d'un coup.
