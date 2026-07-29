# 🔴 AUDIT DE SÉCURITÉ - BLOCKERS CRITIQUES

**Date**: 2026-07-29  
**Status**: ⚠️ **1 blocker restant** — mis a jour le 2026-07-29  
**Verdict**: 2 des 3 blockers fermes (PR #52). Reste l'idempotence.

---

## ✅ BLOCKER #1 — FERME (PR #52) : PAS DE CLOISONNEMENT INTER-BARS

### Problème
N'importe quel utilisateur authentifié peut accéder et modifier les données de n'importe quel bar. Le `bar_id` vient du body de la requête, jamais du contexte d'authentification.

### Preuve d'exploit
```bash
# Serveuse du bar_A s'authentifie avec son jeton
TOKEN=$(curl -X POST https://siptrack-api.onrender.com/api/auth/jeton/ \
  -d "username=serveuse_A&password=..." | jq -r .token)

# Elle ouvre un service chez bar_B (qu'elle n'a pas le droit de gérer)
curl -X POST https://siptrack-api.onrender.com/api/services/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bar_id": "bar_du_voisin_B",
    "responsable_id": "serveuse_A",
    "fond_de_caisse": 50000
  }'

# → HTTP 201 Created ✗ (devrait être 403 Forbidden)
```

### Cause root
- `OuvrirServiceInputSerializer` (service_ventes/interface/rest/serializers.py) accepte `bar_id` en paramètre
- `OuvrirServiceUseCase` le reçoit sans validation
- Pas de check "ce compte appartient-il à ce bar ?"

### Fichiers affectés
- `Backend/contexts/service_ventes/interface/rest/serializers.py` (OuvrirServiceInputSerializer)
- `Backend/contexts/service_ventes/application/use_cases/ouvrir_service.py` (pas de validation)
- Même pattern dans `catalogue/`, `credit_creances/`, `stock_inventaire/`

### Solution requise
```python
# Dans chaque use case (avant toute action)
if commande.bar_id not in compte.bars_accessibles:
    raise PermissionDenied(f"Compte {compte.id} n'a pas accès à {commande.bar_id}")
```

---

## ✅ BLOCKER #2 — FERME (PR #52) : CAPACITÉS AUTO-DÉCLARÉES

### Problème
Les capacités viennent du client et ne sont jamais validées. N'importe qui peut déclarer avoir n'importe quelle capacité.

### Preuve d'exploit
```bash
# Serveuse normale sans droit particulier
curl -X POST https://siptrack-api.onrender.com/api/services/{id}/cloture/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "capacite": "superviseuse",  # ← elle ne l'a PAS
    "raison": "Service fini"
  }'

# → HTTP 200 OK ✗ (elle n'aurait PAS dû pouvoir faire ça)
```

### Cause root
- `gouvernance_acces` context vient d'être crée (hier, revision récente)
- Bar + Compte agrégats existent
- **MAIS** ils ne sont jamais appelés pour valider. Les use cases reçoivent `capacite: string` du body et l'acceptent aveuglément.

### Code affecté
Tous les use cases acceptent `capacite` en paramètre mais ne font jamais :
```python
compte.verifier_capacite(commande.capacite)  # ← N'EXISTE NULLE PART
```

### Solution requise
```python
# Dans chaque handler (OuvrirServiceHandler, ClotureServiceHandler, etc.)
def cloture_service(self, commande: ClotureServiceCommand):
    compte = self._comptes.par_id(commande.compte_id)
    compte.verifier_capacite("superviseuse")  # ← Lève exception si pas la capacité
    
    # Ensuite : logique métier
    service.cloture()
```

---

## 🔴 BLOCKER #3 — OUVERT : PAS D'IDEMPOTENCE (APP MOBILE = DOUBLONS)

### Problème
L'application mobile est **offline-first** (vu dans le README). Quand elle se reconnecte :
1. Elle envoie POST `/api/services/{id}/ventes/`
2. Timeout réseau
3. Client retry automatique (normal)
4. **Même requête envoyée 2 fois**
5. **2 ventes créées au lieu d'1**
6. Journal immuable les enregistre toutes deux
7. **Corruption permanente des données**

Le journal ne peut pas "effacer" un doublon.

### Cause root
Aucune `idempotency_key` implémentée. Chaque POST crée directement sans déduplicate.

### Fichiers affectés
- `Backend/shared/infrastructure/journal/models.py` (MouvementModel)
- Tous les use cases qui écrivent dans le journal

### Solution requise
```python
# Dans MouvementModel
class MouvementModel(models.Model):
    idempotency_key = models.CharField(unique=True, null=True, blank=True)
    # Seule combinaison (mouvement_type, bar_id, idempotency_key) crée

# Dans chaque handler
if self._journal.existe_mouvement_avec_cle(idempotency_key):
    return self._journal.retrouver_mouvement(idempotency_key)

# Créer le mouvement
mouvement = self._journal.enregistrer(..., idempotency_key=commande.idempotency_key)
```

---

## 🟠 PROBLÈMES GRAVES (NON-BLOCKERS MAIS GRAVES)

### Swagger UI Publique
- **Fichier**: `/api/doc/` servie sans authentification
- **Impact**: N'importe qui voit le contrat complet de l'API (endpoints, schémas, paramètres)
- **Recommandation**: Placer derrière `IsAuthenticated` permission

### Stock & Inventaire = Coquille Vide
- **État**: 911 lignes de code dans `contexts/stock_inventaire/`
- **Réalité**: Seuls models + repository + views. Zéro logique métier.
- **Manque**:
  - Mouvements de stock (entrée/sortie/casse/offert)
  - Inventaire physique
  - Conservation de la matière (invariant #6)
- **Conséquence**: Ne peut pas tracer où va la marchandise
- **Recommandation**: Priorité faible (peut être omis en préproduction) ou implémenter complètement

### MyPy Désactivé
- **État**: Complètement en commentaire dans `pyproject.toml`
- **Impact**: Pas de vérification de types → bugs non détectés
- **Recommandation**: Réactiver au moins pour le domaine pur

---

## ✅ POINTS POSITIFS

- ✅ **Journal immuable fortement protégé** - triggers PostgreSQL + SHA-256 + chaînage. Le cœur qui tient.
- ✅ **203 tests passent** - qualité de la couche domaine solide
- ✅ **Authentification correcte** - Token bien dérivé du jeton, auteur_id prouvé
- ✅ **Architecture respectée** - DDD propre, pas de violation d'imports
- ✅ **CI/CD fonctionne** - bloque vraiment, déploiement automatique après

---

## 📋 PLAN DE CORRECTION PRIORITAIRE

| Priorité | Tâche | Durée | Effort |
|---|---|---|---|
| ✅ FAIT | Cloisonnement bar | — | PR #52 |
| ✅ FAIT | Capacités appliquées | — | PR #52 |
| 🔴 P0 | Idempotency_key (journal + dédup) | 2-3j | Moyen (100+ lignes) |
| 🟠 P1 | Swagger sécurisé (IsAuthenticated) | 1j | Faible (5 lignes) |
| 🟠 P2 | Stock & Inventaire minimal (optionnel) | 5-7j | Élevé |

**Estimation totale P0**: 5-8 jours  
**Après P0 : préproduction-ready**

---

## 🎯 RECOMMANDATION

**⚠️ UN BLOCKER RESTE : l'idempotence.**

Le cloisonnement et les capacites sont fermes. L'app mobile etant offline-first,
un rejeu de requete cree encore des doublons que le journal immuable ne peut pas
reparer.

Les 3 blockers rendent l'outil dangereux :
- Données exposées
- Droits escadables
- Doublons irrécupérables

Le PoC est solide architecturalement. Après 5-8 jours de corrections, ce sera un outil fiable.

---

**Audit réalisé par**: Agent Explore  
**Méthodologie**: Analyse statique + tests d'exploit + revue de code
