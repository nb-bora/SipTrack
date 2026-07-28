# Fonctionnalité : Le prix vient du catalogue

## Vue d'ensemble

**Domaine** : Catalogue (nouveau bounded context)
**Acteurs** : Gérante (elle tarife) · Serveuse (elle vend au prix affiché)
**Déclencheur** : Toute vente
**Résultat** : Le prix appliqué **ne dépend pas** de qui saisit

## Le trou que ça ferme

`prix_unitaire` était lu **dans le corps de la requête**, et `produit_id` était une chaîne
libre que rien ne validait. C'est la forme exacte du trou `auteur_id`, fermé en tranche 7 :
une donnée qui fait autorité et qui vient du client.

| | |
|---|---|
| La bière est à **1 000 F** | La serveuse saisit la vente à **600 F** |
| Elle encaisse 1 000 F du client | Elle enregistre un paiement de 600 F |
| `attendu` = 600 | Elle verse 600 |
| **Écart = 0** ✓ | Elle garde 400 F |

La réconciliation de la sous-caisse était **parfaitement équilibrée** : elle compare ce que
la serveuse a *déclaré* encaisser à ce qu'elle remet. En minorant le prix, les deux côtés
bougent ensemble.

> Et le stock ne l'aurait pas attrapé non plus : une bouteille sortie, une bouteille saisie.
> La quantité est juste, seul le prix ment. **Aucun contrôle existant ni planifié ne voyait ça.**

Aujourd'hui, `test_la_sous_caisse_attend_le_vrai_prix` rejoue ce scénario complet : l'attendu
vaut 1 000, l'écart de −400 apparaît, et le manquant devient un Fait.

## Flux principal

```
La gérante tarife
    → POST /api/produits/  { bar_id, nom: "33 Export", prix: 1000 }

La serveuse vend
    → POST .../ventes/  { produit_id, quantite: 3, forme_paiement }
    → le prix est lu au catalogue, copié sur la vente
    ✓ 3 × 1 000 = 3 000, quoi que contienne la requête

La gérante change le tarif
    → POST /api/produits/{id}/tarif/  { prix: 1500 }
    → TarifModifie { ancien: 1000, nouveau: 1500, auteur }
    ✓ les ventes d'hier gardent 1 000
```

## Contrats API

| Route | Effet |
|---|---|
| `POST /api/produits/` | Inscrire un produit et son prix |
| `GET /api/bars/{id}/produits/` | Le catalogue, retirés compris |
| `POST /api/produits/{id}/tarif/` | Changer le tarif — un Fait journalisé |
| `POST /api/produits/{id}/retrait/` | Retirer de la vente, sans supprimer |

### Rupture de contrat assumée

`prix_unitaire` **disparaît** de `POST /api/services/{id}/ventes/`. La vente ne porte plus
qu'un `produit_id` et une quantité. Un `prix_unitaire` envoyé malgré tout est **ignoré**,
pas rejeté — et un test le verrouille.

## Décisions de conception

### Le prix est copié sur la ligne de vente

Pas lu par jointure. Une vente d'hier garde le prix d'hier même si le tarif change ce soir ;
sinon, retarifer réécrirait la valeur de toutes les nuits précédentes — et le journal
raconterait une histoire différente selon le jour où on le lit.

### Un changement de tarif retient l'ancien prix

`TarifModifie` porte l'ancien **et** le nouveau. Sans cette trace, une recette qui baisse
serait indiscernable d'un vol.

### Un produit est retiré, jamais supprimé

Les ventes passées le référencent. L'effacer rendrait illisible l'historique qu'on cherche
précisément à protéger. Il reste au catalogue, marqué `en_vente: false`.

### Le catalogue d'un bar ne fixe pas les prix d'un autre

Un produit d'un autre bar est, depuis un service donné, **inexistant**.

### Réappliquer le même prix est refusé

Un Fait « le prix passe de 1 000 à 1 000 » ne dit rien et pollue le journal.

### Deux fois le même nom est refusé

Deux lignes pour la même bière rendraient tout comptage ambigu — et permettraient d'en tenir
une à un prix minoré.

## Comment les deux contextes se parlent

Service & Ventes et Catalogue **ne se connaissent pas** (ADR-0005).

```
service_ventes.application.ports.TarifDuProduit   ← le port, en son vocabulaire
                     ▲
config/tarifs.py::TarifViaCatalogue               ← composition root, seul
                     ▼                               endroit voyant les deux
catalogue.domain.repositories.ProduitRepository
```

Même motif que `config/creances.py` pour le crédit. L'adaptateur traduit les exceptions
(`ProduitRetireDeLaVente` → `ProduitNonVendable`) : aucun vocabulaire étranger ne franchit
la frontière.

## Événements produits

```
ProduitInscrit          TarifModifie            ProduitRetire
├─ produit_id           ├─ produit_id           ├─ produit_id
├─ bar_id               ├─ bar_id               ├─ bar_id
├─ nom                  ├─ ancien_prix          └─ auteur_id
├─ prix                 ├─ nouveau_prix
└─ auteur_id            └─ auteur_id
```

## Erreurs possibles

| Code | Exception | Raison |
|---|---|---|
| 400 | ValidationError | Prix ≤ 0, nom manquant |
| 404 | ProduitIntrouvable | Le produit n'existe pas |
| 409 | ProduitDejaInscrit | Ce nom figure déjà au catalogue du bar |
| 409 | TarifInchange | Le prix proposé est déjà en vigueur |
| 409 | ProduitNonVendable | Vente d'un produit inconnu, d'un autre bar, ou retiré |

## Chemins de test

- `test_produit_domain.py` — inscription, retarification, retrait
- `test_catalogue_api.py` — bout en bout, dont **`test_la_sous_caisse_attend_le_vrai_prix`**
  qui rejoue le vol devenu impossible

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `produit.py` · `events.py` · `exceptions.py` |
| **Application** | `gerer_le_catalogue.py` · `queries.py` |
| **Infrastructure** | `ProduitModel` (migration `0001`) |
| **Interface** | `views.py` — produits, tarif, retrait, catalogue |
| **Liaison** | `service_ventes/application/ports.py::TarifDuProduit` · `config/tarifs.py` |

## Hors périmètre

- **Prix par variante** (bouteille / casier), promotions, happy hours
- **Prix d'achat et marge** : relèvent de Stock & Inventaire
- **Catégories de produits**
- **Historique des tarifs consultable** : les `TarifModifie` sont au journal, mais aucune
  vue ne les restitue encore

---

**Statut** : ✅ LIVRÉ (branche `feat/catalogue-produits`, ticket #41)
**Tests** : 17 ajoutés (5 domaine · 12 API) · 6 fichiers de tests existants adaptés
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports 5/5 ✓ + 191 tests ✓
**Dernière mise à jour** : 2026-07-28
