# 01 — Langage ubiquitaire (Ubiquitous Language)

Le vocabulaire partagé du domaine. **Chaque terme a un seul sens**, dans le code comme dans
les échanges. Les noms français sont ceux du domaine et doivent être repris tels quels dans
le code (classes, méthodes, événements).

> Règle de langage : on ne dit **jamais** « le stock ». C'est trop vague. On dit *pleins*,
> *vidanges*, *casiers* ou *consignes* — quatre concepts distincts.

> Convention de nommage : les **identifiants de code** (classes, événements, objets-valeurs)
> sont écrits en **ASCII sans accent** (ex. `PrixDate`, `EcartConstate`, `CasseDeclaree`,
> `PerteMonetaireConstatee`). C'est volontaire et conforme aux bonnes pratiques Python — les
> accents et la casse française ne subsistent que dans le **texte**, jamais dans les
> identifiants. La graphie retenue est **`PrixDate`** (et non `PrixDaté`) partout.

## Produits et contenants

| Terme | Définition stricte |
|---|---|
| **Produit** | Une référence vendable (ex. « 33 Export 65cl »). Un concept, pas une bouteille physique. Porte un `Conditionnement`, un `PrixDate`, une valeur de consigne. |
| **Bouteille** | L'unité physique de vérité. Existe *pleine* ou *vide*. |
| **Plein** | Bouteille pleine, vendable. |
| **Vidange** | Bouteille vide, consignée, portant une valeur récupérable. |
| **Casier** | Contenant plastique. **Actif consigné distinct** des bouteilles qu'il porte. |
| **Conditionnement** | Nombre de bouteilles par casier, **propre à un produit** (jamais « 12 » en dur). |
| **Vidange étrangère** | Vide d'une marque non reprise par le distributeur : encombre sans valeur. |

## Argent

| Terme | Définition stricte |
|---|---|
| **Montant** | Une somme **et sa forme**. Un montant sans forme n'a pas de sens. |
| **Forme de paiement** | *Espèces*, *Mobile Money*, ou *Crédit*. Trois registres réconciliés séparément. |
| **Fond de caisse** | Capital de départ laissé (parfois) pour faire la monnaie / rembourser. |
| **Recette** | L'argent qu'une serveuse verse à la clôture de son service. |
| **Prélèvement** | Retrait des recettes par la gérante ou le propriétaire. **Événement obligatoire.** |
| **Dépense** | Sortie d'argent sans marchandise (glace, gaz, transport…). |

## Ventes et service

| Terme | Définition stricte |
|---|---|
| **Service** | Période de responsabilité d'une personne, de l'ouverture (état des lieux) à la clôture (versement). |
| **État des lieux** | Constat du stock à l'ouverture d'un service. |
| **Addition** | Ensemble des consommations d'une table servies mais pas encore réglées. |
| **Encours** | Montant non payé d'une addition. Plafonné (voir `Plafond d'encours`). |
| **Plafond d'encours** | Montant maximal configurable qu'une addition peut atteindre sans paiement. Atteint → paiement obligatoire pour continuer. |
| **Sous-caisse serveuse** | L'activité monétaire d'une serveuse dans un service (son fond, ses tables, sa recette). Son argent lui est **imputable**. |
| **Offert** | Boisson sortie gratuitement (maison/protocole). Décision réservée, autorisée **avant**. |
| **Casse** | Boisson perdue par bris. Déclarée **après** + preuve. |
| **Bouteille emportée** | Plein sorti sans générer de vidange sur place (consigne à la charge du client). |

## Acteurs et gouvernance

| Terme | Définition stricte |
|---|---|
| **Propriétaire** | Détient le(s) bar(s). Voit tout, contrôle la gérante. Ici : l'utilisateur lui-même. |
| **Gérante** | Administre, paramètre, valide, arbitre. **Rôle variable** selon les jours. |
| **Gérante temporaire** | Serveuse laissée en charge d'un service : autorité déléguée, sauf décisions réservées. |
| **Serveuse** | Sert et encaisse en salle. Verse sa propre recette. |
| **Capacité** | La « casquette » sous laquelle un acte est posé (opératrice / superviseuse). L'attribution se fait **par acte et par capacité, jamais par rôle figé**. |
| **Politique de crédit** | Règles permanentes fixées par la gérante (clients autorisés, plafonds) qu'une serveuse applique. |
| **Distributeur** | Circuit brasserie (SABC, Guinness) : livre, reprend vidanges/casiers, prête des actifs. Partie externe. |
| **Fournisseur** | Autres biens sans consignation. Partie externe. |
| **Client** | Consomme, prend à crédit, emporte, rembourse. Partie externe. |

## Contrôle et audit

| Terme | Définition stricte |
|---|---|
| **Mouvement** | Le **fait métier atomique**, immuable, daté, attribué. Le grain du journal. |
| **Journal** | La suite append-only des Mouvements. **Seule vérité** du système. |
| **État** | Une projection calculée du journal (stock, caisse, créances…). Jamais saisi. |
| **Écart** | Différence entre un état *compté* et un état *attendu*. |
| **Contre-passation** | Correction d'une erreur par un **nouveau** Mouvement qui annule le précédent, visible. On n'efface jamais. |
| **Réconciliation** | Confrontation des états comptés et attendus à la clôture (argent) ou à l'inventaire (stock). |
| **Inventaire** | Comptage physique du stock, déclenché **à la demande + surprise** (pas systématique). |
| **Consigne** | Dette de contenant : ce qu'on doit (client emporte) ou ce qu'on nous doit (vides/casiers détenus). Suivie en **quantité ET valeur**. |
| **Scellé** | État terminal d'un service : plus aucun Mouvement ne peut s'y ajouter. |
