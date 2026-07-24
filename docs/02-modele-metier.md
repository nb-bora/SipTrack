# 02 — Modèle métier

Le domaine de SipTrack, décrit indépendamment de toute technologie. Prérequis :
[le glossaire](./01-glossaire-ubiquitaire.md).

## 1. Contexte figé (décisions de découverte)

| Dimension | Choix |
|---|---|
| Type de bar | **Bar d'ambiance / terrasse** (consommation sur place, serveuses, additions) |
| Périmètre | **Boissons uniquement** (pas de nourriture en V1) |
| Chaîne de confiance | **Complète** : propriétaire → gérante → serveuse |
| Encaissement | **Mixte** : caisse + serveuses en salle |
| Circuit du stock | **Pot commun** : service libre sur stock partagé |
| Versement | **Individuel** : chaque serveuse verse sa propre recette |
| Responsabilité service | **Une seule responsable désignée** (gérante ou gérante temporaire) |
| Rémunération serveuses | **Salaire fixe**, indépendant des ventes |
| Taille | **Petit** (1-2 serveuses), affluence variable |
| Déploiement | **Outil interne**, 2-3 bars, données **privées** |

## 2. Philosophie

**La confiance ne se décrète pas, elle se prouve.** On ne surveille pas les gens, on rend
les faits incontestables. **Personne n'échappe au journal, pas même le propriétaire.** La
caissière/serveuse honnête est *prouvée* honnête — c'est ce qui rend l'outil adoptable.

## 3. Acteurs et responsabilités

Principe : **tout Mouvement a un répondant unique** ; l'attribution se fait **par acte et
par capacité**, jamais par rôle figé (la gérante peut être opératrice un jour, superviseuse
le lendemain).

### Délégation à trois niveaux

| Régime | Décisions | Qui décide |
|---|---|---|
| **Réservé** (escalade obligatoire) | Casser un prix / remise · Offert · Grosse dépense | La vraie gérante |
| **Sous politique** | Le **crédit** (accorder/refuser) | La serveuse, selon la `Politique de crédit` |
| **Pleinement délégué** | Ventes, encaissements, réception courante | La serveuse seule |

### Redevabilité

| Objet / Fait | En répond | Devant |
|---|---|---|
| Tout Fait d'un service | La personne **en charge** (gérante temporaire) | La gérante / le propriétaire |
| La sous-caisse d'une serveuse | La **serveuse** | La personne en charge |
| Le paramétrage prix/produits | La **gérante** | Le propriétaire |
| Les validations | La **gérante** | Le propriétaire |
| Le prélèvement | Gérante / **Propriétaire** | (soumis au journal) |
| L'exactitude d'une livraison | Le **distributeur** + le réceptionnaire | La gérante |

## 4. Bounded contexts

| Contexte | Rôle | Type |
|---|---|---|
| **Service & Ventes** | Service, sous-caisse, addition, vente, réconciliation | 🟢 Cœur |
| **Stock & Inventaire** | Pleins/vidanges/casiers, mouvements, inventaire | 🟢 Cœur |
| **Crédit & Créances** | Client, crédit, politique de crédit, remboursements | 🟢 Cœur |
| **Approvisionnement** | Livraison, distributeur/fournisseur, consigne valorisée | 🟡 Support |
| **Catalogue & Tarification** | Produit, prix daté, conditionnement | 🟡 Support |
| **Gouvernance & Accès** | Acteurs, rôles, délégation, validations | ⚪ Générique |
| **Rapports & Consolidation** | Projections gérante / propriétaire / multi-bar | 📊 Lecture |

## 5. Objets métier

- **Stock = 4 compteurs distincts** : pleins, vidanges, casiers, consignes.
- **Agrégats** : `Service`, `Addition`, `SousCaisseServeuse`, `Credit`, `Livraison`,
  `Inventaire` (petits, référencés par identité — voir
  [ADR-0004](./decisions/0004-petits-agregats-coherence-eventual.md)).
- **Objets-valeurs** : `Montant` (valeur + forme), `Quantite` (bouteilles/casiers +
  conditionnement), `PrixDate`, `Attribution`, `Motif`, `Preuve`, `PlafondEncours`.
- **Créance de consigne** : la valeur des vides + casiers détenus = ce que le distributeur
  te doit.

## 6. Événements métier (catalogue)

**Service** : `ServiceOuvert` · `ServiceCloture` · `ServiceScelle` · `ResponsabiliteTransmise`

**Entrée de stock** : `LivraisonRecue` · `LivraisonValidee` · `LivraisonContestee` ·
`MarchandiseAchetee` (dépôt) · `PromotionRecue`

**Sortie de stock** : `VenteEnregistree` · `BouteilleEmportee` · `OffertAutorise` ·
`CasseDeclaree` · `ProduitPerime`

**Argent** : `PaiementRecu` (espèces/MoMo) · `PaiementPartiel` · `CreditAccorde` ·
`RemboursementRecu` · `DepenseEngagee` · `PrelevementEffectue` · `FondDeCaisseApporte` ·
`ArgentConverti` · `PerteMonetaireConstatee`

**Contenants** : `VidangesRendues` · `ConsigneRecupereeParClient` · `CasierPerdu`

**Contrôle** : `InventaireEffectue` · `EcartConstate` · `MouvementContrePasse` · `FaitValide`

> ❌ Il n'existe **pas** d'événement « consommation personnel » : *quiconque boit paie* et
> est traité en client. Les seules sorties non payantes sont `OffertAutorise` (avant) et
> `CasseDeclaree` (après + preuve).

## 7. Cycles de vie

- **Service** : `Ouvert → En cours → Clôturé → Scellé` (terminal).
- **Addition** : `Ouverte → (paiements partiels) → Réglée` | `→ Abandonnée` (→ perte attribuée).
- **Crédit** : `Né → (partiels / rééchelonné) → Soldé` | `→ Passé en perte` (**décision
  gérante, au cas par cas** — jamais automatique).
- **Livraison** : `Reçue → Validée` | `→ Contestée`.
- **Consigne (bouteille emportée)** : `Ouverte → Retournée` | `→ Perdue`.
- **Inventaire** : `Lancé → Compté → Rapproché (écart) → Clôturé`.

## 8. Invariants (règles d'or)

1. **Immutabilité** : un Mouvement ne se modifie ni ne se supprime ; correction = contre-passation visible.
2. **Non-anonymat** : aucun Fait sans attribution. Personne au-dessus du journal.
3. **Primauté des Faits** : on ne modifie jamais un état, on ajoute un Fait.
4. **Zéro inexpliqué** : tout écart, même minime, est **résolu par une écriture** (jamais
   balayé sous un seuil de tolérance). Voir note ci-dessous.
5. **Quiconque boit paie.**
6. **Conservation de la matière** : `pleins sortis = vidanges + emportés + casse`.
7. **Conservation de l'argent** : tout écart de caisse s'explique par un Fait.
8. **Unité de vérité = la bouteille** ; le casier est un actif suivi à part.
9. Une serveuse **ne clôture pas sa sous-caisse tant que toutes ses tables ne sont pas saisies**.
10. `encours d'une addition ≤ plafond configurable`.
11. **Prix daté** : une vente porte le prix en vigueur à l'instant où elle survient.
12. **Continuité + scellement** : tout instant appartient à un seul service ; un service
    scellé n'accepte plus de Fait.
13. **Reconstructibilité** : tout état est recalculable à toute date en rejouant le journal.

## 9. Architecture de contrôle

Attribution à **deux plans** :

- **L'argent descend jusqu'à la serveuse** (chacune verse sa propre recette).
- **Le stock s'arrête au service** (pot commun → non attribuable à une serveuse), porté par
  la responsable désignée.

Deux réconciliations emboîtées :

- **Par serveuse (argent)** : `recette versée` vs `ventes saisies réglées`.
- **Au service (stock + total)** : `stock sorti` vs `Σ ventes + offerts + casse + emportés`.

**Ce que ça attrape, et sa limite (à assumer) :**

- ✅ Niveau serveuse : « a saisi une vente et gardé le cash » (contrôle **quotidien**, sur l'argent).
- ⚠️ Niveau service seulement : « a vendu sans saisir » (vente au noir) — **collectivement**,
  et **uniquement lors d'un inventaire physique**. La clôture nocturne ne portant que sur
  l'argent, **la vente au noir reste invisible entre deux inventaires surprise**.
  → L'**inventaire surprise fréquent et inopiné** est l'ancre anti-vol principale.

> Corollaire à communiquer : une clôture « caisse OK » **ne signifie pas** « aucun vol ».
> La vérité du stock vient des inventaires.

## 10. Rapports attendus

- **Gérante (quotidien)** : bilan du service · crédits en cours & retards · ruptures à venir ·
  **journal complet de la journée**.
- **Propriétaire (de loin)** : recette par bar · coulage consolidé · **prélèvements de la
  gérante** · comparaison entre bars.

## 11. Points ouverts (à trancher plus tard)

1. L'« état des lieux » d'ouverture est-il un comptage réel ou une reprise du théorique ?
2. Saisonnalité (matchs, fêtes, fins de mois) pour juger un écart « anormal ».
3. Consolidation multi-bar concrète (indicateurs de comparaison).
