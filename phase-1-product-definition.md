# Phase 1 — Product Definition

## 1. Le problème résolu

Les compagnies d'assurance traitent des milliers de sinistres. Le processus manuel est lent, coûteux et sujet aux erreurs. Les opérateurs passent du temps à :
- Lire des descriptions non structurées
- Chercher les informations manquantes
- Prioriser les cas à risque vs. les cas simples

**Notre plateforme démontre** comment l'IA peut automatiser l'extraction, le tri et l'analyse des sinistres tout en gardant un humain dans la boucle pour les décisions critiques.

---

## 2. Utilisateurs cibles

| Persona | Rôle | Besoin principal |
|---|---|---|
| **Ops Agent** | Employé opérations | Traiter les sinistres rapidement, avoir une vue claire |
| **Ops Manager** | Responsable équipe | Superviser les KPIs, identifier les goulots |
| **Customer** | Assuré | Soumettre un sinistre, suivre son traitement |

---

## 3. User Journey — Customer

```
1. Customer remplit le formulaire de sinistre
2. Le système stocke et affiche "Sinistre reçu"
3. L'IA extrait les informations structurées
4. L'IA identifie les informations manquantes
5. L'agent IA pose des questions de suivi
6. Le client répond → l'IA met à jour le dossier
7. Le sinistre passe en analyse de risque
8. Le score de risque est attribué
9. Le sinistre est orienté vers le bon workflow
10. Le client reçoit le statut final
```

---

## 4. User Journey — Ops Agent

```
1. Voit le tableau de bord avec tous les sinistres
2. Filtre par risque élevé / en attente / à réviser
3. Ouvre un sinistre → voit tout : texte brut, extraction IA, score, recommandation
4. Prend une décision : Approuver / Demander plus d'info / Escalader / Rejeter
5. L'action est enregistrée dans l'audit trail
```

---

## 5. MVP Scope

### Must-have (MVP)

- Formulaire de soumission de sinistre (texte libre + champs structurés)
- Extraction IA des informations (LLM → JSON structuré)
- Détection des informations manquantes
- Agent IA avec workflow de questions de suivi
- Moteur de scoring de risque (règles + signaux)
- Classification Low / Medium / High Risk
- Dashboard opérations (tableau, filtres, détail sinistre)
- Actions humaines (Approuver / Escalader / Rejeter)
- Audit trail des actions
- Métriques d'impact business

### Nice-to-have (post-MVP)

- Upload de documents/images
- Authentification multi-utilisateurs
- Détection d'anomalie avancée (ML)
- Notifications email
- Export de rapports

### À reporter

- Intégration avec des assureurs réels
- Paiement de sinistres
- Application mobile

---

## 6. Différenciation vs. un simple chatbot

| Chatbot classique | Notre plateforme |
|---|---|
| Répond à des questions | Gère un workflow complet de bout en bout |
| Pas d'état | L'agent suit l'état du sinistre |
| Pas de risque/scoring | Moteur de risque avec signaux expliqués |
| Pas d'humain dans la boucle | Human-in-the-loop pour les décisions critiques |
| Pas de métriques | Dashboard avec impact business mesurable |
| Pas d'audit | Trail complet de toutes les actions |

---

## 7. Impact business mesurable

| Métrique | Avant (manuel) | Après (plateforme) |
|---|---|---|
| Temps moyen de traitement | 25 min | 8 min |
| Taux d'automatisation | 0% | ~40% |
| Cas nécessitant revue humaine | 100% | ~18% |
| Informations manquantes détectées | Tardivement | Immédiatement |
| Détection de fraude | Manuelle | Automatisée + expliquée |
