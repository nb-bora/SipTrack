# ADR-0006 — L'autorisation se décide à la frontière, jamais dans la requête

**Statut** : accepté — 2026-07-29
**Contexte** : ticket #51

## Le problème

Deux champs arrivaient dans le corps des requêtes et décidaient des droits :

- `bar_id` — *où* j'agis. Jamais confronté aux bars où l'appelant a un compte.
- `capacite` — *ce que* j'ai le droit de faire. Jamais confronté aux capacités
  réellement accordées.

Un compte authentifié pouvait donc ouvrir un service, inscrire un produit ou
lire les créances de **n'importe quel bar**, et se déclarer superviseuse pour
clôturer une caisse qu'il n'avait pas le droit de toucher.

`Compte.verifier_capacite()` existait pourtant, et `CompteModel` portait les
capacités accordées. Mais l'appel n'était fait que dans Gouvernance lui-même :
partout ailleurs, c'était du code mort.

C'est exactement la faille déjà corrigée pour `auteur_id`. Une déclaration n'est
pas une preuve.

## La décision

**Un port, un adaptateur, un point d'application.**

```
contexts.*.interface.rest.views
        │  exiger(request, bar_id=…, capacite=…)
        ▼
shared.interface.rest.acces          ← traduit un refus en 403
        │
        ▼
shared.application.controle_acces    ← le port (Protocol)
        ▲
        │  branché par config.container
        │
contexts.gouvernance_acces.infrastructure.controle_acces
```

C'est le motif déjà employé pour `TarifDuProduit` et `OuvertureDeCreance` : les
contextes ne s'importent pas, la composition root branche. Les cinq contrats
d'architecture restent verts.

### Le cloisonnement tombe de la recherche elle-même

Un compte n'existe que pour un couple *(bar, utilisateur)* — la contrainte
d'unicité l'impose en base. Chercher le compte de l'appelant dans un bar où il
n'a rien à faire ne trouve rien, et rien vaut refus.

Aucun test d'appartenance séparé : c'est ce qui rend le garde difficile à
contourner par oubli.

### Ce que le client ne déclare plus

`capacite` a disparu des entrées publiques. La **qualité** inscrite au journal
(opératrice / superviseuse) se déduit désormais des capacités réelles : est
superviseuse celle qui peut clôturer un service, puisque clôturer est l'acte qui
fige les écarts de la soirée.

Laisser ce champ déclaratif aurait permis de signer une soirée « opératrice »
tout en agissant en supervision — et un registre qu'on annote à sa guise n'est
plus un registre.

## Ce qui a été écarté

**Contrôler dans les cas d'usage (couche application).** Plus orthodoxe en DDD,
et à l'abri d'un futur appelant non-HTTP. Écarté pour l'instant : cela imposait
d'injecter le port dans 18 handlers, de réécrire leur construction dans huit
fichiers de test et d'ajouter une traduction exception → 403 sans gestionnaire
global. Pour la même garantie sur le seul point d'entrée qui existe aujourd'hui.

> **Ce choix a un coût.** Un futur appelant — commande d'administration, tâche
> de fond, import — contournerait le garde. La protection retenue contre cela
> n'est pas un principe mais un test : `test_aucun_endpoint_ne_repond_a_un_inconnu`
> énumère les routes déclarées et échoue si l'une répond à qui n'a de compte
> nulle part. Le jour où un appelant non-HTTP apparaît, le contrôle devra
> descendre dans la couche application.

**Un `capacite` distinct par lecture.** Aucune capacité de lecture n'existe dans
l'énumération. En inventer une par endpoint aurait produit une liste que
personne n'aurait tenue à jour. Lire exige d'**appartenir** au bar ; écrire
exige une capacité nommée.

## Conséquences

- `CapaciteRequise` (dans `shared`) reflète `CapaciteAtomique` (dans
  Gouvernance) : une vue doit nommer ce qu'elle exige sans importer Gouvernance.
  La duplication est verrouillée par un test d'égalité stricte des deux
  ensembles.
- Un objet **introuvable** reste un 404, conformément au contrat publié. Un
  objet qui **existe ailleurs** donne 403. Masquer l'absence protégerait d'une
  énumération d'UUID, qui n'est pas praticable — on ne paie pas une réponse
  trompeuse pour un gain nul.
- Les fixtures de test créent désormais un bar et un compte réels : agir quelque
  part suppose d'y tenir un compte, y compris en test.
