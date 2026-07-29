# Audit : ce qui reste à construire

> État au 2026-07-28 · `main` à 191 tests, 5 contrats d'architecture, zéro issue SonarQube.
> Contextes livrés : Service & Ventes, Crédit & Créances, Catalogue.

---

## Avertissement liminaire

Tu demandes un backend « complet, sans plus jamais rien ajouter ». Ce n'est pas atteignable et
il faut le dire : un outil qui vit voit son métier bouger. Ce qui **est** atteignable, et ce
que ce document vise : un état où **plus rien de structurel ne manque** — où les ajouts futurs
sont des variations sur des motifs déjà en place, pas des refontes.

La différence tient à une chose : les trous listés en Partie 1 et 2 ne sont pas des
fonctionnalités manquantes, ce sont des **failles**. Tant qu'elles sont là, ajouter des
fonctionnalités par-dessus revient à bâtir sur du sable.

---

## Partie 1 — Le trou structurel : `bar_id` vient de la requête

**C'est la troisième occurrence du même motif.** Deux ont déjà été fermées :

| Donnée | Venait de | Fermé par |
|---|---|---|
| `auteur_id` | le corps de la requête | Tranche 7 — vient du jeton |
| `prix_unitaire` | le corps de la requête | Ticket #41 — vient du catalogue |
| **`bar_id`** | **le corps de la requête** | **❌ ouvert** |

Aujourd'hui, n'importe quel compte authentifié peut :

```
POST /api/services/   { "bar_id": "le-bar-du-voisin", ... }   → ouvre un service chez lui
GET  /api/bars/le-bar-du-voisin/encours/                      → lit ses créances clients
POST /api/produits/   { "bar_id": "le-bar-du-voisin", ... }   → tarife son catalogue
```

Il n'y a **aucun cloisonnement** entre bars. Et il ne peut pas y en avoir, parce que —
second constat — **l'entité `Bar` n'existe pas**. `bar_id` est une chaîne libre que rien ne
valide, ne rattache à personne, et ne relie à aucun propriétaire.

C'est exactement ce que ta question sur les comptes présuppose comme existant. Ça n'existe pas.

---

## Partie 2 — L'autorisation : état réel, néant

Réponse directe à ta question : **non, l'autorisation n'est pas gérée du tout.**

Ce qui existe :

- ✅ **Authentification** — jeton DRF, `IsAuthenticated` par défaut sur toutes les routes
- ✅ **Attribution** — chaque Fait porte l'auteur authentifié, prouvé

Ce qui n'existe pas :

- ❌ Aucune permission au-delà de « es-tu connecté ? ». Le seul `BasePermission` du projet
  protège la page Swagger.
- ❌ Le contexte `gouvernance_acces` est **une coquille** : un endpoint de connexion, pas de
  domaine, pas d'application, pas d'infrastructure.
- ❌ `Capacite` (`operatrice` / `superviseuse`) existe dans `shared/domain/attribution.py`,
  mais elle est **déclarative et auto-déclarée** : celle qui ouvre un service annonce sa
  capacité dans le corps de la requête. Rien ne la vérifie. C'est une étiquette, pas un droit.

Conséquence concrète : **une serveuse peut clôturer le service, retarifer la bière, éteindre
la créance d'un client, et consulter les encours de tous les bars de la plateforme.**

---

## Partie 3 — Ton idée : la gérante définit les limites de chaque rôle

### Ce qui est juste

L'instinct est le bon, et il rejoint le modèle métier, qui parle déjà d'« acteurs, rôles,
**délégation**, validations ». Un jeu de rôles figé dans le code serait une erreur : deux bars
ne s'organisent pas pareil, et une gérante qui ne peut pas déléguer contourne l'outil en
partageant son mot de passe — ce qui détruit d'un coup l'invariant de non-anonymat.

**Mais tel quel, le principe se retourne contre l'outil.** Quatre réserves.

### 1. Il faut un socle que personne ne peut abaisser

Si *tout* est configurable, alors les garanties que l'outil existe pour offrir deviennent
optionnelles. La première chose que ferait une gérante malhonnête serait de s'accorder le
droit d'effacer.

Certaines choses doivent rester impossibles **à tout le monde, propriétaire compris** :

- modifier ou supprimer un Fait (déjà tenu : triggers PostgreSQL + chaînage SHA-256)
- saisir au nom de quelqu'un d'autre
- faire disparaître un écart sans écriture

> Invariant 2 du modèle : « Personne au-dessus du journal. » Un système de droits entièrement
> configurable contredit cet invariant, sauf s'il est explicitement borné par un socle.

Le configurable vient **par-dessus** ce plancher, jamais en dessous.

### 2. Un changement de droit est lui-même un Fait

Sans ça : j'accorde un droit → la personne agit → je retire le droit. Il ne reste rien. Le
journal doit contenir « X a donné le droit Y à Z, le … » avec la même immuabilité que le reste.

C'est la condition pour que la question « qui **pouvait** faire ça, ce soir-là ? » ait une
réponse. Sans elle, l'outil répond « qui a fait quoi » mais plus « qui avait le droit ».

### 3. Le droit s'évalue à l'instant de l'acte, et se fige avec lui

Un droit accordé aujourd'hui ne légitime pas un acte d'hier. La permission doit être évaluée
au moment du Fait, et **la capacité sous laquelle on a agi doit être copiée sur le Fait** —
exactement comme le prix est copié sur la vente.

Bonne nouvelle : `Attribution(auteur_id, capacite, horodatage)` a été conçue pour ça dès le
départ. Elle est aujourd'hui décorative ; il s'agit de lui donner sa fonction.

### 4. La séparation des tâches ne se délègue pas entièrement

Si la même personne encaisse et valide son propre versement, le contrôle est un théâtre.
Le système n'a pas forcément à l'interdire — mais il doit **le constater et l'écrire** :
« versement reçu et validé par la même personne ». Une gérante seule dans son bar est un cas
légitime ; ce qui ne l'est pas, c'est que ça ne se voie pas.

### Ma recommandation

Un modèle à **trois étages** :

```
┌─ SOCLE ────────────── immuable, dans le code, personne ne l'abaisse
│  · un Fait ne se modifie ni ne s'efface
│  · nul n'agit au nom d'un autre
│  · nul écart ne disparaît sans écriture
├─ RÔLES ────────────── définis par la gérante, par bar
│  · elle compose des rôles à partir de capacités atomiques
│  · chaque composition est un Fait journalisé
└─ DÉLÉGATION ───────── ponctuelle, datée, révocable
   · « ce soir, Marie supervise » — et ça s'écrit
```

Et une règle de nommage : les capacités portent des **noms métier** (`encaisser`,
`cloturer_un_service`, `accorder_un_credit`), jamais des noms techniques (`POST /services`).
Une gérante doit pouvoir lire ses propres réglages.

---

## Partie 4 — Inventaire par domaine

### Gouvernance & Accès — ⚪ quasi tout
| Manque | Pourquoi ça compte |
|---|---|
| Agrégat `Bar`, avec un propriétaire | Rien n'existe aujourd'hui ; prérequis de tout le reste |
| Inscription d'un propriétaire, création de bars | Ton scénario d'entrée |
| Comptes employés rattachés à un bar | Aujourd'hui, comptes Django globaux |
| Capacités atomiques + rôles composables | Cf. Partie 3 |
| Délégation datée et révocable | Le modèle la nomme explicitement |
| **Cloisonnement par bar, appliqué partout** | La faille de la Partie 1 |
| Validations (double regard sur les actes sensibles) | Nommé par le modèle |

### Stock & Inventaire — 🟢 tout
L'ancre anti-vol principale, et **le seul contrôle qui attrape « vendu sans saisir »**.

| Manque |
|---|
| Mouvements de stock (entrée, sortie, casse, offert, transfert) |
| Inventaire physique et son écart |
| Conservation de la matière : `pleins sortis = vidanges + emportés + casse` (invariant 6) |
| Casiers et consignes comme actifs suivis à part (invariant 8) |
| Réconciliation « stock sorti vs Σ ventes » — la seconde réconciliation emboîtée |

### Approvisionnement — 🟡 tout
Livraisons, fournisseurs, consigne valorisée, rapprochement bon de livraison / facture.

### Rapports & Consolidation — 📊 tout
Projections gérante, propriétaire, multi-bar. Aucune vue agrégée n'existe aujourd'hui.

### Service & Ventes — 🟢 livré, lacunes ciblées
| Manque | Invariant concerné |
|---|---|
| **Scellement** — `SCELLE` existe dans l'enum, aucun code ne l'utilise | 12 |
| **Continuité** — rien n'empêche deux services de se chevaucher | 12 |
| **Offerts, casse, consommation du personnel** | 5 — « quiconque boit paie » |
| **Résolution d'un écart** (justification, contre-passation, mise à charge) | 4, 7 |
| **Contre-passation** — le principe est documenté, le geste n'existe pas | 1 |
| Abandon d'une addition (départ sans payer) | — |
| Garde-fou sous-caisse : bloquer le versement si des tables ne sont pas saisies | 9 |

### Crédit & Créances — 🟢 livré, lacunes connues
| Manque | Invariant |
|---|---|
| Plafond d'encours configurable | 10 |
| Passage en perte (« décision gérante, jamais automatique ») | — |
| Politique de crédit (qui peut accorder, jusqu'à combien) | dépend de Gouvernance |

### Catalogue — 🟡 livré, lacunes connues
| Manque |
|---|
| Conditionnement : bouteille / casier (invariant 8) |
| Vue d'historique des tarifs — les `TarifModifie` sont au journal, rien ne les restitue |
| Prix d'achat et marge (relève d'Approvisionnement) |

### Journal — ✅ solide, une lacune
| Manque | Invariant |
|---|---|
| **Rejeu** : reconstruire un état à une date donnée | 13 — « reconstructibilité » |

Le journal est immuable, chaîné, vérifiable (`verifier_journal`). Mais rien ne sait le
**rejouer**. L'invariant 13 est aujourd'hui une intention, pas une capacité.

---

## Partie 5 — Les invariants du modèle, tenus ou non

| # | Invariant | État |
|---|---|---|
| 1 | Immutabilité | ✅ triggers PostgreSQL + chaînage SHA-256 |
| 2 | Non-anonymat | ✅ authentification + `auteur_id` prouvé |
| 3 | Primauté des Faits | ✅ journal append-only |
| 4 | Zéro inexpliqué | ⚠️ l'écart est **constaté**, jamais **résolu par une écriture** |
| 5 | Quiconque boit paie | ❌ offerts et consommation du personnel non modélisés |
| 6 | Conservation de la matière | ❌ Stock absent |
| 7 | Conservation de l'argent | ⚠️ l'écart est constaté, son explication n'existe pas |
| 8 | Unité = la bouteille | ❌ pas de conditionnement |
| 9 | Sous-caisse bloquée si tables non saisies | ⚠️ tenu au niveau du service, pas par serveuse |
| 10 | Plafond d'encours | ❌ |
| 11 | Prix daté | ✅ ticket #41 |
| 12 | Continuité + scellement | ❌ `SCELLE` décoratif, chevauchement non contrôlé |
| 13 | Reconstructibilité | ⚠️ le journal contient tout, rien ne le rejoue |

**4 tenus sur 13.** C'est cohérent avec l'avancement — mais c'est la mesure honnête de ce
qui reste.

---

## Partie 6 — Le non-fonctionnel

| Manque | Gravité | Pourquoi |
|---|---|---|
| **Idempotence des écritures** | 🔴 | L'app mobile est *offline-first* : elle rejouera ses requêtes. Sans clé d'idempotence, une reconnexion crée des ventes en double. Rien n'existe. |
| **Cloisonnement multi-bar** | 🔴 | Cf. Partie 1 |
| Pagination des listes | 🟠 | `GET /encours/`, catalogue : aucune. Un bar chargé fera tomber le mobile. |
| Limitation de débit globale | 🟠 | Seule la connexion est freinée |
| Sauvegardes et restauration | 🔴 | Un journal inaltérable sur un disque unique reste un journal perdable |
| Observabilité (logs structurés, erreurs) | 🟠 | Aucun outillage |
| Rétention / RGPD | 🟡 | Noms de clients, dettes : durée de conservation non décidée |
| Déploiement (CI → prod, migrations) | 🟠 | La CI teste, rien ne déploie |
| Jeu de données de démonstration | 🟡 | Utile pour la recette et la formation |

---

## Partie 7 — Ordre recommandé

L'ordre n'est pas négociable sur les deux premiers : tout le reste s'appuie dessus.

### 1. Gouvernance & Accès — le socle 🔴
`Bar` + propriétaire + comptes rattachés + cloisonnement appliqué partout.
**Ferme la faille de la Partie 1.** Sans lui, chaque fonctionnalité ajoutée est une porte de
plus sur les données des autres bars.

### 2. Capacités et rôles 🔴
Socle non négociable, rôles composables par la gérante, délégation datée, chaque changement
de droit journalisé. `Attribution.capacite` cesse d'être décorative.

### 3. Idempotence des écritures 🔴
Avant que l'app mobile n'existe. Après, il sera trop tard : les doublons seront déjà en base,
et ils sont irréparables dans un journal immuable.

### 4. Stock & Inventaire 🟢
La seconde réconciliation. Le gros morceau, et la raison d'être de l'outil.

### 5. Résolution des écarts + contre-passation 🟢
Ferme l'invariant 4. Aujourd'hui l'outil sait dire « il manque 400 F » mais pas « voici
pourquoi ». Un écart qu'on ne peut pas résoudre finit par être ignoré.

### 6. Scellement et continuité 🟠
Invariant 12.

### 7. Offerts, casse, consommation du personnel 🟠
Invariant 5. Nécessaire pour que la réconciliation du stock tombe juste.

### 8. Rapports & Consolidation 📊
Une fois les Faits complets, les vues sont mécaniques.

### 9. Approvisionnement 🟡

### 10. Rejeu du journal 🟡
Invariant 13. Peut venir tard : le journal contient déjà tout ce qu'il faut.

---

## Ce que ça donne à l'arrivée

En tenant cet ordre, tu obtiens un backend où :

- les trois questions de l'outil ont une réponse : **qui a fait quoi**, **qui pouvait le
  faire**, **où est passée la marchandise**
- les 13 invariants du modèle sont tenus par du code, pas par des intentions
- ce qui reste relève de la variation : un nouveau type de mouvement, un nouveau rapport,
  un nouveau moyen de paiement — chacun suivant un motif déjà éprouvé trois fois

C'est ça, « complet ». Pas « fini ».
