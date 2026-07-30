# Contexte Complet pour Lovable — Frontend Prêt à l'Emploi

**Status:** ✅ Backend-Frontend Parfaitement Alignés (33/33 endpoints)  
**Date:** 2026-07-30  
**Audience:** Lovable pour implémentation UI

---

## TL;DR

La couche API du frontend est **100% synchronisée** avec le backend. Chaque endpoint backend a un wrapper typé, les types correspondent, l'idempotence est gérée automatiquement. Lovable peut construire les routes UI sans se soucier de divergences API.

---

## État de l'API Frontend

### Fichiers Clés

```
Frontend/
├── src/api/
│   ├── client.ts          # Bas niveau : lire(), ecrire()
│   ├── endpoints.ts       # 33 wrappers typés
│   ├── types.ts           # 33+ interfaces TypeScript
│   └── ecriture.ts        # Hook useEcriture() pour idempotence
├── etat/
│   └── session.ts         # Gestion jeton & bar
└── routes/
    ├── connexion.tsx      # Login (utilise authJeton)
    ├── accueil.tsx        # Page accueil
    ├── bars.tsx           # Gestion bars
    ├── ...
```

### Principaux Helpers Disponibles

#### Authentification (Publique)
```typescript
// Login
const rep = await authJeton(username: string, password: string);
// → { token: string }

// Signup (nouveau compte + premier bar)
const rep = await inscrire(
  username: string, 
  password: string, 
  nom_bar: string, 
  email?: string
);
// → { user_id, bar_id, bar_nom, message }

// Logout (revoque le jeton)
const mutation = useEcriture();
await mutation('POST', '/api/auth/deconnexion/', undefined, { cle });
```

#### Bars & Accès
```typescript
// Les bars OU L'ON PEUT TRAVAILLER : ceux que l'on possède ET ceux où l'on
// tient un compte. Ne pas présumer la possession à l'écran — un employé y
// figure sans rien posséder. Distinguer les deux suppose GET /api/moi/ (#67).
const bars = await listerBars(); // → Bar[]
await creerBar(nom: string);      // → Bar
const acces = await listerAcces(barId: string); // → AccesEntree[]

// Gestion comptes
await creerCompte(bar_id, user_id, capacites_initiales);
await ajouterCapacite(compteId, capacite);
await retirerCapacite(compteId, capacite);
```

#### Catalogue
```typescript
const produits = await listerProduits(barId);
await creerProduit(bar_id, nom, prix);
await tariferProduit(produit_id, prix);
await retirerProduit(produit_id);
```

#### Service & Ventes (Le Cœur)
```typescript
// Ouvrir un service (journée de vente)
const service = await ouvrirService(bar_id, fond_de_caisse);

// Lire l'état du service
const service = await getService(service_id);

// Enregistrer une vente
await enregistrerVente(serviceId, {
  produit_id,
  quantite,
  forme_paiement: 'especes' | 'mobile_money' | 'credit',
  addition_id?: string
});

// Ouvrir une addition (table)
const addition = await ouvrirAddition(serviceId, table_numero);

// Encaisser un paiement
await encaisserPaiement(serviceId, additionId, {
  montant,
  forme_paiement,
  client_id?: string
});

// Régler l'addition
await reglerAddition(serviceId, additionId);

// Clôturer le service
await cloturerService(serviceId);
```

#### Inventaire & Stock
```typescript
const produits = await listerStock(barId); // Stock vs Catalogue
await inscrireStock(bar_id, nom, quantite_initiale);
await ajusterStock(produitId, quantite);
await vendreStock(produitId, quantite);
await corrigerInventaire(produitId, quantite_nouvelle, raison);
```

#### Clients & Créances
```typescript
await creerClient(bar_id, nom);
const encours = await getEncoursClient(clientId);
const tousLesEncours = await listerEncoursBar(barId);
await rembourserCredit(creditId, montant);
```

#### Caisse (Versement)
```typescript
const soussCaisses = await listerSousCaisses(serviceId);
// Structure: { serveuse_id, encaisse_especes, encaisse_mobile_money, verse, ecart }

await verserRecette(serviceId, montant);
```

---

## Contrats & Conventions

### Idempotence (Cruciale)
**Tous les mutations (POST, PUT, DELETE) doivent être idempotentes.**

```typescript
import { useEcriture } from '@/api/ecriture';

function MonComposant() {
  const mutation = useEcriture();
  
  async function creerBar() {
    const rep = await mutation('POST', '/api/bars/', { nom: 'Bar du coin' });
    // La clé idempotence est générée UNE FOIS et réutilisée sur retry
    // Si une erreur 409 "requête en cours" survient, elle retry auto après 1.5s
    // La clé ne change que si la requête réussit (201/200)
  }
}
```

**Pourquoi:** Le backend trace chaque acte (écriture) dans un journal append-only. Une même clé = un seul fait créé, même avec rejeu.

### Authentification
- **Schème:** `Authorization: Token <jeton>` (PAS Bearer)
- **Stockage:** `localStorage.jeton`
- **Refresh:** Pas de refresh_token. Les jetons n'expirent pas (app offline-first)
- **Revocation:** `POST /api/auth/deconnexion/` supprime le jeton côté serveur
- **Routes publiques:** `POST /api/inscription/`, `POST /api/auth/jeton/` (aucun token requis)

### Types & Montants
- **Montants/Tarifs:** Toujours en entiers (XAF — pas de floats)
- **Formes paiement:** `'especes' | 'mobile_money' | 'credit'`
- **Statuts service:** `'ouvert' | 'cloture' | 'scelle'`
- **Statuts addition:** `'ouverte' | 'reglee' | 'abandonnee'`
- **Capacités:** 14 valeurs enum (voir `types.ts`)

### Query Strings
- Toujours encodés : `?bar_id=${encodeURIComponent(barId)}`
- Jamais collision avec paramètres de chemin

### Erreurs Standard
- **400:** Validations échouées → `{ champ: [messages] }` (DRF)
- **401:** Token invalide → purge `jeton` ET `bar` du localStorage
- **403:** Capacité manquante → détail de l'opération refusée
- **404:** Ressource introuvable
- **409:** Conflit métier (bar dupliqué, créance déjà remboursée, etc.)
- **429:** Rate-limited (route jeton seulement)

---

## Routes Existantes & Utilisation

### Authentification
- `/connexion` — Login (utilise `authJeton`)
  - TODO: Route `/inscription` pour self-signup (utiliserait `inscrire()`)

### Gestion Bar
- `/bars` — Lister/créer bars
- `/bars/{bar_id}/acces` — Journalisation des consultations plateforme

### Exploitation Quotidienne
- `/accueil` — Tableau de bord
- `/tables` — Ouvrir service, voir additions ouvertes
- `/tables/{addition_id}` — Détail addition, paiements, règlement
- `/vente` — Enregistrer consommations
- `/catalogue` — Gérer produits (prix, retrait)
- `/inventaire` — Stock vs consommé
- `/equipe` — Comptes & capacités (qui fait quoi)
- `/recette` — Versement espèces/mobile
- `/creances` — Qui doit quoi
- `/cloture` — Clôturer le service
- `/reglages` — Config bar & users

### Audit
- `/journal-acces` — Qui a consulté quoi (trace plateforme)

---

## Décisions Architecturales Clés

### 1. Clean Architecture + DDD
Le backend suit Clean Arch avec contextes métier (bounded contexts) :
- `gouvernance_acces` — Bars, comptes, droits
- `catalogue` — Produits
- `service_ventes` — Cœur du métier
- `credit_creances` — Dettes & remboursements
- `stock_inventaire` — Tracking physique

Chaque contexte a son propre modèle de domaine, use cases, et interface REST.

### 2. Journal Append-Only
Chaque acte (vente, paiement, création bar, etc.) crée un **Fait** immuable journalisé. Les lectures recalculent l'état (CQRS).

Conséquence : L'idempotence n'est pas optionnelle — elle est le fondement du système.

### 3. Pas de Comptes Plateforme
⚠️ **Contrainte majeure:** Aucun compte de la plateforme n'écrit dans un bar, jamais.

- Les admins peuvent *lire* (mais pas *écrire*)
- Les écritures viennent toujours d'un compte du bar
- Cela préserve la traçabilité complète

### 4. Offline-First Mobile
- Jetons sans expiration (app offline)
- Chaque appareil a son jeton (changement de device = nouveau jeton)
- Idempotence clés = resynchro après reconnexion

### 5. CORS : absent du backend — le frontend passe par un relais

⚠️ **Correction d'une affirmation antérieure de ce document.** Il était écrit ici
que backend et frontend étaient co-hostés, donc sans problème CORS. C'était une
supposition, et elle est fausse. Vérification faite : le backend n'a ni
`corsheaders` dans `INSTALLED_APPS`/`MIDDLEWARE`, ni aucun réglage CORS. Un
preflight `OPTIONS` sur `/api/inscription/` répond 200 **sans aucun en-tête
`Access-Control-*`** — tout appel cross-origin est donc bloqué par le navigateur.

**En développement**, un relais Vite (`vite.config.ts`) transmet `/api` vers
`http://127.0.0.1:8000`. `VITE_API_URL` est laissé **vide** pour que les URLs
restent relatives, donc de même origine : la question du CORS ne se pose plus, au
lieu d'être contournée.

**Conséquence pour la production :** si l'API y est servie depuis un autre domaine
que l'app, il faudra du CORS côté backend — le relais Vite est un outil de dev,
absent du bundle de production. À traiter par un ticket backend.

**Symptôme si l'on repointe `VITE_API_URL` directement vers l'API :** `fetch` lève
un `TypeError` et l'app affiche « Le service est injoignable. Vérifiez votre
connexion. » alors que le serveur est parfaitement sain. Ce message ne distingue
pas une panne réseau d'un blocage CORS — c'est une piste de confusion connue.

---

## Tâches pour Lovable

### Phase 1: Routes Essentielles (MVP)
- [ ] Affiner `/connexion` — actuel : login only. Ajouter toggle → `/inscription`?
- [ ] Implémenter `/accueil` — Dashboard bars/service
- [ ] Routes `/tables` & `/tables/{aid}` — POS (point of sale)
- [ ] Route `/vente` — Enregistrer consommations

### Phase 2: Complétude Métier
- [ ] `/catalogue` — CRUD produits
- [ ] `/inventaire` — Stock tracking
- [ ] `/equipe` — Comptes & capacités
- [ ] `/creances` — Gestion dettes

### Phase 3: Polish & Audit
- [ ] `/cloture` — Clôture service + calculs
- [ ] `/recette` — Versement caisse
- [ ] `/reglages` — Config
- [ ] `/journal-acces` — Audit trail

---

## Points d'Attention pour Lovable

### API Quirks
1. **DELETE avec Body** — `DELETE /api/comptes/{cid}/capacites/` prend un body JSON (`{ capacite }`)
   - Inhabituel mais correct. Utiliser `ecrire()` qui supporte ça.

2. **Idempotence Clé** — Générée comme UUID v4, réutilisée sur retry
   - Ne pas en générer une nouvelle par request
   - `useEcriture()` gère ça automatiquement

3. **Query String dans GET** — `GET /api/inventaire/produits/?bar_id=...`
   - Le `bar_id` est requis, pas optionnel
   - Encoder les spéciaux (`encodeURIComponent`)

4. **Token Scheme** — Pas Bearer, c'est `Token <jeton>` (espace, pas "Bearer")

### State Management
- `jeton` stocké dans `localStorage.jeton`
- `bar` (bar courant) stocké dans `localStorage.bar`
- Sur 401, purger TOUS LES DEUX
- `useSession()` hook available pour lire jeton/bar

### Types à Connaître
```typescript
// Clés énums
type FormePaiement = 'especes' | 'mobile_money' | 'credit';
type StatutService = 'ouvert' | 'cloture' | 'scelle';
type StatutAddition = 'ouverte' | 'reglee' | 'abandonnee';

// Capacités (14 au total)
type Capacite = 
  | 'ouvrir_service' | 'enregistrer_vente' | 'encaisser'
  | 'verser_recette' | 'cloturer_service' | 'creer_client'
  | 'accorder_credit' | 'encaisser_remboursement'
  | 'inscrire_produit' | 'tarifer' | 'retirer_produit'
  | 'creer_compte' | 'accorder_capacite' | 'retirer_capacite'
  | 'composer_role' | 'deleguer';
```

### Validation Frontend vs Backend
- Validation **métier** (business rules) → Backend seulement
- Validation **forme** (email format, min/max) → Frontend + Backend
- Montants doivent rester entiers (jamais float)

---

## Prochaines Étapes

1. ✅ API alignment complet
2. → Lovable implémente les routes UI
3. → QA teste les flows métier (vente, paiement, clôture)
4. → Déploiement staging & tests offline
5. → Go live

---

## Contacts & Ressources

- **Documentation Technique:** Voir `/Backend/docs` et `/Frontend/docs`
- **Audit Alignement:** `Frontend/docs/11-audit-alignement-parfait.md`
- **Matrice Complète:** `Frontend/docs/alignment-matrix.md` (dans scratchpad)
- **Contrat API:** `Frontend/docs/09-harmonisation-frontend-backend.md`

---

## Historique des Corrections

| Date | Correction | Impact |
|---|---|---|
| Initial | ❌ Audit invalide (0 divergences reportées) | Faux positif |
| 2026-07-30 | Découverte: `POST /api/inscription/` manquant | +1 endpoint |
| 2026-07-30 | Découverte: `POST /api/auth/deconnexion/` manquant | +1 endpoint |
| 2026-07-30 | Implémentation + vérification finale | ✅ 33/33 |

---

**Lovable est prêt à implémenter. Aucune synchronisation supplémentaire n'est nécessaire.**
