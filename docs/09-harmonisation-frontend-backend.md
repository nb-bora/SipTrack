# Harmonisation Frontend ↔ Backend

**Date:** 2026-07-30  
**Statut:** Frontend aligné au contrat API exact. Trois trous mineurs du backend identifiés.

---

## ✅ Corrections apportées au Frontend

### 1. **Idempotence : clé stable par intention** (🔥 critique)

Le backend exige un `Idempotency-Key` sur chaque écriture pour garantir qu'un double envoi ne produit qu'un seul Fait. **L'ancien code régénérait la clé à chaque appel**, transformant un simple réessai en doublon — exactement ce qu'on cherche à éviter.

**Nouvelle approche :**
- Créé `src/api/ecriture.ts` : hook `useEcriture()` qui gère la clé
- La clé naît avec le formulaire, sert à tous les réessais, et n'est renouvelée qu'au succès
- Un écart au serveur libère la clé (le middleware la supprime) : la réutiliser est sans danger
- 15 routes mises à jour pour utiliser `useEcriture()` au lieu de `useMutation()` brut

**Fichiers modifiés :**
- `src/api/ecriture.ts` (nouveau)
- `src/routes/accueil.tsx`, `bars.tsx`, `cloture.tsx`, `catalogue.tsx`, `creances.$clientId.tsx`, `equipe.tsx`, `inventaire.tsx`, `recette.tsx`, `tables.tsx`, `tables.$aid.tsx`, `vente.tsx`

### 2. **URL avec query string** (bug)

L'ancienne fonction `url()` ajoutait le slash final *après* la requête (`?bar_id=abc/`), ce qui cassait le paramètre.

```typescript
// Avant (cassé)
GET /api/inventaire/produits/?bar_id=abc/  // Le slash avait bouffé le paramètre

// Après (correct)
GET /api/inventaire/produits/?bar_id=abc
```

### 3. **401 libère aussi le bar** (sécurité)

Un 401 (jeton invalide/révoqué) purkire maintenant le `barId` stocké : inutile de redémarrer la session avec un contexte bar pourri.

### 4. **Formulations clarifiées**

- **Recette :** Explication explicite que l'attendu couvre *uniquement les tables*, pas les ventes au comptoir
- **Crédit au comptoir :** Retiré du sélecteur ; expliqué pourquoi (pas de débiteur désigné)
- **Sélecteur de client :** Clarifiait que un nom connu sera retrouvé, pas dupliqué
- **Nettoyage des tables :** Fixé un bug dans `tables.tsx` où l'effet se rejouait sans fin à cause d'une dépendance instable

---

## ⚠️ Trois trous du backend — comment les gérer

### A. Pas de `GET /api/services/` ni `GET /api/services/{id}/additions/`

Le frontend **pallie par du localStorage** :
- Conserve le dernier `service_id` ouvert par bar
- Mémorise localement les additions ouvertes depuis cet appareil
- Rafraîchit chacune par `GET /api/services/{sid}/additions/{aid}/`
- **Avertissement honnête** : « Seules les tables ouvertes depuis cet appareil apparaissent ici »

C'est un compromis fonctionnel aujourd'hui, mais mauvaise UX si l'utilisatrice change de téléphone. À corriger avec deux query services simples dès que possible.

### B. Pas de `GET /api/auth/jeton/` → `{token, utilisateur_id, capacites}`

L'API rend seulement `{token}` après l'auth. **Le frontend ne sait donc pas ce que l'utilisatrice peut faire.**

Approche actuelle : afficher **tous les boutons**, traiter le `403` comme le mode normal de refus :
```typescript
// src/hooks/useCapacites.ts
export function useCapacites() {
  return { peut: (_c: Capacite) => true, connues: false };
}
```

Notice en cas de 403 : « Vous n'avez pas la capacité pour cette action » (en clair, pas dramatique).

**Prêt pour le futur :** Ce hook est le seul point d'entrée ; un endpoint `/api/auth/jeton/` enrichi se branchera en une ligne.

### C. `DELETE /api/comptes/{id}/capacites/` exige un corps JSON

C'est inhabituel pour un DELETE. Le frontend l'envoie correctement (`{ capacite: "..." }`), mais documenter que c'est voulu au backend.

---

## 📋 État de conformité

| Aspect | Status | Notes |
|--------|--------|-------|
| **Types TypeScript** | ✅ | Dérivés du contrat, français, aucune invention |
| **Endpoints mappés** | ✅ | 32 routes frontend implémentées |
| **Idempotence** | ✅ | Clé stable, réessai automatique sur 409 « en cours » |
| **Authentification** | ✅ | Token Bearer ? Non. **Token classique** (« `Authorization: Token <jeton>` »). Correct. |
| **Formatage montants** | ✅ | `12 500 FCFA` (entiers, espace insécable) |
| **Langage** | ✅ | Français partout, accents OK (labels), pas d'ASCII requis (ça c'est pour le code) |
| **Trous API paliés** | ✅ | localStorage, 403 mode normal, hook d'extension |
| **Requête cherche le serveur correct** | ✅ | `VITE_API_URL` en env var |

---

## 🎯 Avant de mettre en prod

### Backend
1. **Ajouter CORS** : `django-cors-headers` + configuration pour l'origine du frontend
2. *(Optionnel mais recommandé)* Ajouter `GET /api/services/?bar_id=...` query service
3. *(Optionnel mais recommandé)* Ajouter `GET /api/services/{id}/additions/` query service
4. *(Optionnel mais recommandé)* Enrichir `/api/auth/jeton/` pour retourner capacités + `utilisateur_id`

### Frontend
- Définir `VITE_API_URL` en `.env.local` (ex. `http://127.0.0.1:8000`)
- Vérifier que localStorage fonctionne (pas de CSP trop stricte)
- Tester avec le backend local : créer un bar, ouvrir un service, enregistrer une vente

---

## 📝 Fichiers clés

**Couche API (contrat) :**
- `src/api/types.ts` — Types TypeScript du contrat
- `src/api/endpoints.ts` — Wrappers typés sur les 32 endpoints
- `src/api/client.ts` — Client HTTP unique (auth, erreurs typées, idempotence)
- `src/api/ecriture.ts` — **Hook pour gérer la clé d'idempotence**

**Domaine (formatage, libellés) :**
- `src/domaine/format.ts` — XAF (montants entiers), dates
- `src/domaine/libelles.ts` — Traductions des énumérations
- `src/domaine/erreurs.ts` — Traduction des codes HTTP en messages utilisateur

**État (mémoire locale, session) :**
- `src/etat/local.ts` — localStorage : dernier service, additions locales
- `src/etat/session.ts` — État global : jeton, bar courant

**Routes (UI complet) :**
- 13 écrans : connexion, bars, accueil, vente, tables, créances, catalogue, inventaire, équipe, recette, clôture, journal d'accès, réglages

---

## 🧪 Test basique

```bash
# Terminal 1 : backend
cd Backend
python -m pytest
uvicorn config.asgi:application --reload

# Terminal 2 : frontend
cd Frontend
export VITE_API_URL=http://127.0.0.1:8000
npm run dev

# Navigateur
# Créer compte via backend
# Connexion sur localhost:5173
# Créer bar, ouvrir service, enregistrer vente, encaisser, clôturer
```

Tout doit marcher de bout en bout. Les doublon-clics doivent être protégés (idempotence).
