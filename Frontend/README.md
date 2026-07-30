# Registre du Bar

# SipTrack — Frontend web (application de gestion de bar)

Construis une application web React + TypeScript + Tailwind + shadcn/ui qui consomme

une API REST Django existante. **L'API existe déjà et ne doit pas être modifiée ni

simulée : respecte son contrat au caractère près.** N'invente aucun endpoint, aucun

champ, aucun nom de propriété.

---

## 1. Le produit

SipTrack est « le registre incontestable du bar ». C'est un outil interne de gestion

et d'audit pour des bars d'ambiance au Cameroun. Utilisatrices réelles : une

propriétaire, une gérante, des serveuses. Terrain : téléphone Android d'entrée de

gamme, réseau instable, forte luminosité ou pénombre, usage debout et pressé.

Principe fondateur, à refléter dans toute l'interface : **le journal des faits est la

seule vérité ; tous les états sont calculés, jamais saisis.** Concrètement, l'interface

n'invente jamais un chiffre, ne « corrige » jamais un total localement, et n'efface

jamais rien. Elle affiche ce que l'API rend, et elle affiche les écarts au lieu de

les lisser.

### Vocabulaire — obligatoire dans toute l'UI (français, termes exacts)

| Terme | Sens |

|---|---|

| **Service** | Période de responsabilité d'une personne, de l'ouverture à la clôture. |

| **Addition** | Consommations d'une table, servies mais pas encore réglées. |

| **Fond de caisse** | Capital de départ laissé en caisse pour faire la monnaie. |

| **Recette** | L'argent qu'une serveuse verse à la clôture de son service. |

| **Sous-caisse** | L'activité monétaire d'une serveuse dans un service : ce qu'elle a encaissé, ce qu'elle a versé, l'écart. |

| **Écart** | Différence entre le compté et l'attendu. Jamais masqué. |

| **Encours** | Ce qu'un client doit encore. |

| **Créance** | Une dette précise, née d'une addition réglée en crédit. |

| **Capacité** | Le droit nommé de poser un acte précis (`enregistrer_vente`, `encaisser`…). |

N'utilise **jamais** les mots « cash », « bill », « check », « stock » (trop vague),

« user », « order ». Pas d'anglais dans l'interface. Les libellés portent les accents ;

les identifiants de code n'en portent pas.

Monnaie : **franc CFA (XAF)**. Tous les montants de l'API sont des **entiers**, sans

décimale. Affiche-les formatés `12 500 FCFA` (espace insécable comme séparateur de

milliers). N'utilise jamais de nombre à virgule, ne divise jamais par 100.

---

## 2. Contraintes techniques non négociables

### 2.1 Base de l'API

L'URL de base vient d'une variable d'environnement `VITE_API_URL` (ex.

`http://127.0.0.1:8000`). Toutes les routes sont préfixées par `/api/`.

**Toutes** les URLs de l'API se terminent par un slash `/` — ne le retire jamais,

Django redirige et la redirection casse les POST.

### 2.2 Authentification

- `POST /api/auth/jeton/` avec `{ "username": "...", "password": "..." }`

  → `200 { "token": "..." }` ; identifiants faux → `400 { "non_field_errors": [...] }`.

- Cette route est **limitée à 10 tentatives par minute** : au-delà elle rend `429`.

  Affiche alors « Trop de tentatives. Réessayez dans une minute. »

- Toute autre requête porte l'en-tête `Authorization: Token <jeton>`.

  **Le schéma est `Token`, pas `Bearer`.**

- Le jeton **n'expire pas** et il n'y a **pas de refresh token**. Stocke-le dans

  `localStorage`. Un `401` signifie jeton invalide ou révoqué : purge le stockage et

  renvoie à l'écran de connexion.

### 2.3 En-tête `Idempotency-Key` — obligatoire

**Toute** requête `POST`, `PUT`, `PATCH` ou `DELETE` vers `/api/` (sauf

`/api/auth/jeton/`) doit porter un en-tête `Idempotency-Key` contenant un UUID v4.

Sans lui, le serveur répond `400` et l'action est perdue.

Règles précises, à implémenter dans le client HTTP :

- **Un UUID est généré une fois par intention d'écriture**, au moment où l'utilisatrice

  appuie sur le bouton — puis **réutilisé tel quel** pour tous les réessais de cette

  même action. Ne régénère jamais l'UUID lors d'un retry : ce serait créer un doublon

  irrécupérable dans un journal immuable.

- Si la réponse porte l'en-tête `Idempotency-Replayed: true`, l'écriture avait déjà

  abouti : traite-la comme un succès normal, sans message d'erreur.

- `409` sur une écriture peut signifier « requête identique encore en cours » : dans ce

  cas seulement, réessaie automatiquement une fois après 1,5 s avec **la même clé**.

- `422` signifie « cette clé a déjà servi pour une requête différente » : c'est un bug

  du client, affiche une erreur technique explicite.

Encapsule tout ça dans **une seule** fonction `ecrire()` du client API, pour qu'aucun

composant ne puisse l'oublier.

### 2.4 Ce que le frontend n'a pas le droit de faire

Ces interdits ne sont pas stylistiques, ils sont la raison d'être du produit :

- **Ne jamais envoyer un prix.** Le prix vient du catalogue du bar, seule autorité.

  Le formulaire de vente n'a pas de champ prix — il affiche le prix du catalogue en

  lecture seule et envoie uniquement `produit_id`, `quantite`, `forme_paiement`.

- **Ne jamais envoyer un `auteur_id`, `serveuse_id`, `proprietaire_id` ou `capacite`.**

  L'auteur d'un fait est toujours déduit du jeton, côté serveur.

- **Ne jamais recalculer un total localement.** Les totaux d'addition, les restes à

  payer, les encours et les écarts viennent de l'API. Si tu as besoin du total, tu

  relis l'addition.

- **Aucune suppression, aucune modification d'un fait passé.** Pas de bouton

  « supprimer une vente », pas d'édition d'un paiement. Un produit se *retire de la

  vente*, il ne se supprime pas.

- **Ne jamais masquer un écart.** Un écart négatif s'affiche en rouge, un écart positif

  en ambre, zéro en vert — mais les trois s'affichent.

---

## 3. Contrat de l'API — exhaustif

Les codes d'erreur portent tous un corps `{ "detail": "message en français" }`, sauf

les `400` de validation qui portent `{ "champ": ["message", ...] }`.

**Affiche systématiquement le `detail` renvoyé par le serveur** : il est déjà rédigé en

français pour l'utilisatrice finale (« Impossible de clôturer : 3 addition(s) encore

ouverte(s). »). N'écris pas tes propres messages par-dessus.

### Gouvernance & Accès

```

POST   /api/auth/jeton/           { username, password } → { token }

GET    /api/bars/                 → [ { id, nom, proprietaire_id } ]   (mes bars)

POST   /api/bars/                 { nom } → 201 { id, nom, proprietaire_id } | 409

POST   /api/comptes/              { bar_id, user_id, capacites_initiales: string[] }

                                  → 201 { id, bar_id, user_id, capacites: string[] } | 404 | 409

POST   /api/comptes/{id}/capacites/    { capacite } → 200 { ...compte } | 404 | 409

DELETE /api/comptes/{id}/capacites/    { capacite } → 200 { ...compte } | 404 | 409

GET    /api/bars/{bar_id}/acces/  → [ { administrateur_id, operation, horodatage } ]

```

Note : `DELETE /api/comptes/{id}/capacites/` porte **un corps JSON** — c'est

inhabituel, mais c'est le contrat. Et comme c'est une écriture, elle exige aussi

`Idempotency-Key`.

Liste exacte des capacités (valeurs à envoyer, telles quelles) :

`ouvrir_service`, `enregistrer_vente`, `encaisser`, `verser_recette`,

`cloturer_service`, `creer_client`, `accorder_credit`, `encaisser_remboursement`,

`inscrire_produit`, `tarifer`, `retirer_produit`, `creer_compte`, `accorder_capacite`,

`retirer_capacite`, `composer_role`, `deleguer`.

Dans l'UI, affiche-les avec des libellés lisibles (« Enregistrer une vente »,

« Encaisser », « Clôturer le service »…) mais envoie toujours la valeur brute.

### Catalogue — le prix fait autorité

```

GET    /api/bars/{bar_id}/produits/    → [ { id, bar_id, nom, prix, en_vente } ]

POST   /api/produits/                  { bar_id, nom, prix } → 201 | 409

POST   /api/produits/{id}/tarif/       { prix } → 200 | 404 | 409 (prix inchangé)

POST   /api/produits/{id}/retrait/     (pas de corps) → 200 | 404

```

Le catalogue rend aussi les produits retirés, marqués `en_vente: false`. Sur l'écran de

vente, **filtre-les** ; sur l'écran de gestion du catalogue, **affiche-les grisés** avec

la mention « retiré de la vente ».

### Service & Ventes — le cœur

```

POST   /api/services/                         { bar_id, fond_de_caisse }

                                              → 201 { id, bar_id, statut, fond_de_caisse, ouvert_le, clos_le }

GET    /api/services/{id}/                    → 200 { ...service } | 404

POST   /api/services/{id}/cloture/            (pas de corps) → 200 | 404 | 409

POST   /api/services/{id}/ventes/             { produit_id, quantite, forme_paiement, addition_id? }

                                              → 201 { id, service_id, produit_id, quantite,

                                                      prix_unitaire, montant_total, forme_paiement, addition_id }

POST   /api/services/{id}/additions/          { table_numero } → 201 { id, service_id, table_numero, statut, ouvert_le, ferme_le }

GET    /api/services/{id}/additions/{aid}/    → 200 addition détaillée | 404

POST   /api/services/{id}/additions/{aid}/paiements/   { montant, forme_paiement, client_id? }

                                              → 201 { id, addition_id, service_id, montant, forme_paiement, reste_a_payer }

POST   /api/services/{id}/additions/{aid}/reglement/   (pas de corps) → 200 | 404 | 409

POST   /api/services/{id}/versement/          { montant } → 201 { id, service_id, serveuse_id, attendu, verse, ecart }

GET    /api/services/{id}/sous-caisses/       → [ { serveuse_id, encaisse_especes, encaisse_mobile_money, verse, ecart } ]

```

**Addition détaillée** (`GET .../additions/{aid}/`), forme exacte :

```json

{

  "id": "…", "service_id": "…", "table_numero": 4,

  "statut": "ouverte", "ouvert_le": "…", "ferme_le": null,

  "lignes": [ { "vente_id": "…", "produit_id": "…", "quantite": 2,

                "prix_unitaire": 1000, "montant_total": 2000,

                "forme_paiement": "especes", "horodatage": "…" } ],

  "total": 2000,

  "paiements": [ { "paiement_id": "…", "montant": 1000,

                   "forme_paiement": "especes", "horodatage": "…" } ],

  "paye": 1000,

  "reste_a_payer": 1000

}

```

Le `total` est recalculé par le serveur à chaque lecture. **Après toute vente ou tout

paiement sur une addition, relis l'addition** plutôt que de patcher l'état local.

Énumérations, valeurs exactes :

- `forme_paiement` : `especes` | `mobile_money` | `credit`

- `statut` de service : `ouvert` | `cloture` | `scelle`

- `statut` d'addition : `ouverte` | `reglee` | `abandonnee`

Règles métier que l'UI doit rendre visibles :

- La forme `credit` **exige** un `client_id` — sinon `409`. Le sélecteur de client

  n'apparaît que quand `credit` est choisi, et il est alors obligatoire.

  Un paiement en crédit solde l'addition sans qu'aucun argent n'entre : ouvre une

  créance à la place. Dis-le explicitement dans l'UI avant de confirmer.

- Une addition passe à `reglee` **d'elle-même** quand le cumul des paiements atteint le

  total. `POST .../reglement/` n'est utile que pour constater ce règlement ; il rend

  `409` avec « L'addition n'est pas soldée : reste N à encaisser. » si ce n'est pas le

  cas. Ne propose donc « Régler » que si `reste_a_payer === 0`.

- Un paiement supérieur au reste dû rend `409`. Pré-remplis le champ montant avec

  `reste_a_payer` et borne-le à cette valeur.

- La clôture d'un service est **refusée tant qu'une addition reste ouverte** (`409`, le

  message dit combien). Sur l'écran de clôture, dis-le avant de tenter l'appel.

- Le versement de recette : la serveuse verse **pour elle-même**, l'identité vient du

  jeton. L'attendu est la somme de ses encaissements **en espèces uniquement** — le

  mobile money ne se remet pas de la main à la main. Explique-le sur l'écran.

  Un second versement rend `409` « Votre recette a déjà été versée sur ce service. »

- Dans les sous-caisses, `verse` et `ecart` valent `null` tant que la personne n'a pas

  versé : affiche « en attente », pas « 0 FCFA ».

### Crédit & Créances

```

POST   /api/clients/                     { bar_id, nom } → 201 { id, bar_id, nom }

GET    /api/clients/{id}/encours/        → 200 encours | 404

GET    /api/bars/{bar_id}/encours/       → [ encours ]   (la vue de la gérante)

POST   /api/credits/{id}/remboursements/ { montant } → 201 crédit | 404 | 409

```

Forme d'un **encours** :

```json

{ "client_id": "…", "client_nom": "…",

  "total_du": 15000, "total_rembourse": 5000, "reste": 10000,

  "creances": [ { "credit_id": "…", "client_id": "…", "client_nom": "…",

                  "service_id": "…", "addition_id": "…",

                  "montant": 10000, "rembourse": 0, "reste": 10000, "statut": "…" } ] }

```

Créer un client est idempotent côté serveur : un nom déjà connu dans ce bar rend le

client existant plutôt qu'un doublon. Ne préviens pas d'un « doublon », c'est voulu.

La liste `/api/bars/{bar_id}/encours/` **n'inclut pas** les clients dont toutes les

dettes sont éteintes.

### Stock & Inventaire

```

GET    /api/inventaire/produits/?bar_id=…          → [ { id, bar_id, nom, quantite } ]

POST   /api/inventaire/produits/                   { bar_id, nom, quantite_initiale } → 201 | 409

POST   /api/inventaire/produits/{id}/stock/        { quantite } → 200 | 404

POST   /api/inventaire/produits/{id}/vendre/       { quantite } → 200 | 404 | 409

PUT    /api/inventaire/produits/{id}/inventaire/   { quantite_nouvelle, raison } → 200 | 404 | 400

```

Attention : ce contexte est **distinct du catalogue**. Un produit de stock et un produit

de catalogue sont deux objets différents avec deux identifiants différents. Ne les

confonds pas et ne tente pas de les rapprocher automatiquement — présente-les sur deux

écrans séparés (« Catalogue & tarifs » d'un côté, « Inventaire » de l'autre).

La correction d'inventaire exige une **raison en texte libre, obligatoire** : c'est ce

qui rend l'écart opposable. Le champ n'a pas de valeur par défaut et le bouton reste

désactivé tant qu'il est vide.

### Exploitation

```

GET    /api/sante/    → 200 { statut, commit, base } | 503

```

Publique, sans jeton. Utilise-la pour un indicateur discret « service disponible » et

pour distinguer une panne serveur d'un problème de réseau.

---

## 4. Trous connus du backend — comment les gérer

Trois choses manquent aujourd'hui côté API. **Ne les invente pas** : traite-les

exactement comme décrit.

1. **Pas d'endpoint « lister les services d'un bar ».**

   Conserve en `localStorage`, par bar, l'identifiant du dernier service ouvert par

   l'utilisatrice, et relis-le via `GET /api/services/{id}/`. L'écran d'accueil montre

   « Service en cours » ou, à défaut, un bouton « Ouvrir un service ». Prévois une

   saisie manuelle d'identifiant de service en repli, dans un écran de réglages.

2. **Pas d'endpoint « lister les additions d'un service ».**

   Mémorise en `localStorage`, par service, la liste des additions ouvertes créées

   depuis cet appareil (`{ id, table_numero }`), et rafraîchis chacune par

   `GET /api/services/{sid}/additions/{aid}/`. Retire de la liste locale celles dont le

   `statut` n'est plus `ouverte`. Affiche un avertissement honnête sur cet écran :

   « Seules les tables ouvertes depuis cet appareil apparaissent ici. »

3. **Pas d'endpoint « mon compte / mes capacités ».**

   Le frontend ne peut donc pas savoir ce que l'utilisatrice a le droit de faire.

   **Conséquence : n'implémente aucun masquage de bouton fondé sur un rôle.** Affiche

   toutes les actions, et traite le `403` comme le mode normal de refus : une notice

   claire reprenant le `detail` du serveur (« Vous n'avez pas la capacité … »), sans

   dramatisation ni écran d'erreur pleine page.

   Structure malgré tout le code avec un hook `useCapacites()` qui rend aujourd'hui

   « tout est permis, le serveur tranche », pour qu'un futur endpoint se branche à un

   seul endroit.

---

## 5. Écrans à produire

Mobile-first, une colonne, cibles tactiles d'au moins 48 px. Pensé pour être utilisé

d'une main, debout, dans le bruit.

1. **Connexion** — identifiant, mot de passe. Rien d'autre. Pas d'inscription : les

   comptes sont créés par la gérante.

2. **Choix du bar** — `GET /api/bars/`. S'il n'y en a qu'un, passe directement.

   Le bar choisi est mémorisé et conditionne tous les écrans suivants.

3. **Accueil du service** — l'écran central.

   - Pas de service en cours → carte « Ouvrir un service » (fond de caisse en XAF).

   - Service en cours → statut, fond de caisse, heure d'ouverture, et quatre actions

     dominantes : **Vente rapide**, **Tables**, **Verser ma recette**, **Clôturer**.

4. **Vente rapide (comptoir)** — grille des produits du catalogue (`en_vente: true`),

   gros pavés tactiles avec nom et prix. Un appui sélectionne, un pas-à-pas

   quantité (`−` / `+`), puis choix de la forme de paiement, puis confirmation.

   Le montant total est affiché **d'après le prix du catalogue**, en lecture seule, et

   la valeur qui fait foi reste celle rendue par la réponse `201`.

5. **Tables** — liste des additions ouvertes (mécanisme local décrit en §4), bouton

   « Ouvrir une table » (numéro de table).

6. **Détail d'une addition** — l'écran le plus travaillé.

   Numéro de table, statut, lignes de consommation, **total**, paiements déjà encaissés,

   **payé**, **reste à payer** mis en évidence. Deux actions : « Ajouter une

   consommation » (même flux que la vente rapide, avec `addition_id`) et « Encaisser »

   (montant pré-rempli au reste dû, forme de paiement, sélecteur de client si `credit`).

   Quand `reste_a_payer` atteint 0, l'écran bascule visuellement en « soldée » et

   propose « Régler l'addition ».

7. **Verser ma recette** — explication de ce qui est attendu (espèces seulement),

   saisie du montant remis, puis affichage franc du résultat : **attendu / versé /

   écart**. Un écart n'est ni une faute ni une alerte agressive : c'est un fait

   consigné. Formulation neutre, jamais accusatoire.

8. **Clôture du service** — récapitulatif, puis la table des **sous-caisses** :

   par personne, encaissé espèces, encaissé mobile money, versé, écart. Bouton

   « Clôturer », et si le serveur refuse, le message exact sur les additions ouvertes.

9. **Créances** — liste des encours du bar, triée par reste décroissant. Détail d'un

   client : ses créances, et l'encaissement d'un remboursement.

10. **Catalogue & tarifs** — liste des produits, création, changement de tarif

    (avec un rappel : « Les ventes déjà saisies gardent leur prix. Ce changement est

    consigné au journal. »), retrait de la vente.

11. **Inventaire** — liste avec quantités, ajout de stock, correction d'inventaire

    avec raison obligatoire.

12. **Équipe & accès** — création de compte, attribution et retrait de capacités via

    des interrupteurs libellés en clair.

13. **Journal des consultations plateforme** — `GET /api/bars/{bar_id}/acces/`.

    Un écran sobre en lecture seule, présenté ainsi : « Qui, hors du bar, a consulté

    vos données. » C'est un écran de confiance, mets-le en valeur.

---

## 6. Direction artistique

Sobre, dense, sérieux — un registre comptable, pas une application de divertissement.

Aucune illustration décorative, aucun dégradé bavard, aucune animation gratuite.

- **Thème sombre par défaut**, thème clair disponible. Un bar travaille la nuit.

- Contraste élevé (viser AA au minimum, AAA sur les montants) : l'écran est lu à bout

  de bras, parfois en plein soleil.

- **Les montants sont la typographie principale** : chiffres tabulaires, grande taille,

  poids fort. Un reste à payer se lit sans lunettes.

- Palette restreinte : une teinte neutre profonde comme fond, un accent unique pour

  l'action principale, et trois teintes sémantiques réservées aux écarts et statuts

  (vert = soldé/conforme, ambre = en attente/excédent, rouge = manquant/refus).

  N'utilise jamais l'accent pour un statut, ni une teinte sémantique pour un bouton

  neutre.

- États explicites partout : chargement (squelettes, pas de spinner plein écran),

  vide (que faire ensuite), erreur (le `detail` du serveur, et une action de reprise).

- Un bouton d'écriture se désactive pendant sa requête et affiche sa progression.

  Le double-appui est le mode d'usage normal sur ce terrain — l'idempotence protège

  côté serveur, l'UI doit protéger côté perception.

- Confirmation explicite, avec récapitulatif du montant, avant : encaisser un paiement,

  verser une recette, clôturer un service, changer un tarif, corriger un inventaire.

---

## 7. Architecture du code

- Vite + React + TypeScript strict.

- **Un seul module client API** (`src/api/client.ts`) qui porte : URL de base, en-tête

  `Authorization: Token`, génération et réutilisation de l'`Idempotency-Key`, lecture de

  `Idempotency-Replayed`, traduction des codes HTTP en erreurs typées

  (`ErreurValidation` 400, `NonAuthentifie` 401, `AccesRefuse` 403, `Introuvable` 404,

  `Conflit` 409, `CleReutilisee` 422, `TropDeRequetes` 429, `PanneServeur` 5xx).

- **Types TypeScript dérivés du contrat ci-dessus**, dans `src/api/types.ts`, nommés en

  français (`Service`, `Addition`, `AdditionDetail`, `Vente`, `Paiement`, `Versement`,

  `SousCaisse`, `Produit`, `ProduitStock`, `Client`, `Encours`, `Creance`, `Compte`,

  `Bar`). Aucune propriété optionnelle inventée.

- TanStack Query pour les lectures, avec invalidation ciblée après chaque écriture

  (une vente invalide l'addition concernée et le service ; un versement invalide les

  sous-caisses).

- Une couche `src/domaine/` pour le formatage des montants, les libellés des

  énumérations et des capacités. Aucun calcul métier n'y a sa place.

- Pas de state manager global au-delà de : jeton, bar courant, service courant.

**Livre l'application complète et fonctionnelle, avec un `.env.example` documentant

`VITE_API_URL`.**

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://sip-track-register.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/e88127b2-0b54-4e58-8aee-f9a0f7ca88f8).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
