# ADR-0007 — Un compte plateforme lit tout, n'écrit nulle part, et laisse une trace

**Statut** : accepté — 2026-07-29
**Contexte** : besoin de comptes capables d'intervenir sur l'ensemble du système

## La demande, et pourquoi elle ne peut pas être satisfaite telle quelle

« Des comptes superadministrateurs qui ont les droits sur tout le système. »

Un compte capable d'**écrire** dans le journal de n'importe quel bar rend ce
journal contestable. Le jour où une gérante accuse une serveuse d'un manquant de
50 000 FCFA, la défense devient : *« un compte de la plateforme a pu écrire ce
mouvement »*. La chaîne d'empreintes SHA-256 et le déclencheur PostgreSQL qui
refuse les `UPDATE` ne prouveraient plus rien — on aurait construit une porte
blindée et laissé une fenêtre ouverte à côté.

C'est en contradiction directe avec le premier principe du projet : *la confiance
ne se décrète pas, elle se prouve*.

## La décision

Le compte plateforme **consulte** et **administre la plateforme**. Il n'ouvre pas
un service, n'enregistre pas une vente, n'accorde pas un crédit.

| Appelant | Lecture d'un bar | Écriture dans un bar |
|---|---|---|
| Compte du bar | ✅ | ✅ si la capacité est accordée |
| Compte plateforme, **sans** compte dans ce bar | ✅ **et tracée** | ❌ toujours |

### La dérogation est structurelle, pas conditionnelle

Le port `ControleAcces` expose **deux méthodes**, jamais une seule avec un
drapeau :

```python
def exiger_lecture(self, *, auteur_id, bar_id, operation) -> None: ...
def exiger_capacite(self, *, auteur_id, bar_id, capacite, operation) -> Capacite: ...
```

Le privilège vit dans `exiger_lecture` et nulle part ailleurs. `exiger_capacite`
ne le connaît pas. Aucune valeur de paramètre ne fait basculer l'un dans l'autre
— une écriture ne peut donc pas l'atteindre, même par erreur de programmation.

C'est ce qui a motivé la refonte de l'API du garde (ADR-0006) : la convention
`capacite=None` signifiant « lecture » aurait laissé un endpoint d'écriture
glisser du mauvais côté par simple oubli.

### Deux axes de capacités qui ne se croisent jamais

`CapacitePlateforme` (`lire_tout_bar`, `creer_bar_plateforme`, `suspendre_bar`,
`gerer_facturation`) est distincte de `CapaciteAtomique`. Un test vérifie que
l'intersection des deux ensembles est vide : sans lui, un nom présent des deux
côtés ferait qu'une capacité plateforme satisferait un contrôle d'exploitation
par simple coïncidence de chaîne.

## La contrepartie non négociable

Chaque consultation **exercée au titre du privilège** est inscrite dans
`gouvernance_acces_plateforme`, et le propriétaire du bar la lit sur
`GET /api/bars/{bar_id}/acces/`.

> « Je peux voir vos données, et vous voyez quand je les regarde » se défend.
> « Je peux tout voir sans que vous le sachiez » ne se défend pas.

Une lecture faite par quelqu'un qui travaille dans le bar ne produit **aucune**
écriture : le journal des accès répond à « qui, d'extérieur, a regardé mon
bar ». Le noyer sous les lectures ordinaires le rendrait illisible et ferait
payer une écriture à chaque consultation d'une gérante chez elle.

## Ce qui a été écarté

**Inscrire les consultations dans le journal métier.** C'était ma première idée.
`DjangoJournal.enregistrer` prend un **verrou global à toute la plateforme** pour
garantir le chaînage — son propre commentaire précise qu'il sérialise « deux
bars, deux serveuses ». Une requête `GET` de support aurait bloqué les écritures
de tous les autres établissements. Et une consultation n'est pas un Fait
d'exploitation : aucun stock ne bouge, aucun argent ne circule.

Table dédiée, insertion simple, index `(bar_id, -horodatage)` qui sert exactement
la question posée.

**Faire échouer la requête si la trace ne s'écrit pas.** Le compromis va dans
l'autre sens : une trace perdue est un incident, un support incapable de lire
pendant une panne d'écriture en est un plus grave. L'échec part en `error` dans
les logs pour ne pas passer inaperçu.

## Conséquences

- Le chemin courant ne paie rien : la table des comptes plateforme n'est
  consultée **que si** aucun compte n'a été trouvé dans le bar. Pour une
  serveuse dans son bar, une seule recherche, comme avant.
- Suspendre un compte plateforme (`actif = False`) produit son effet
  immédiatement, sans redéploiement.
- `GET /api/bars/{bar_id}/acces/` passe par le garde ordinaire : il faut un
  compte dans le bar pour lire ses accès. Qui consulte quoi renseigne sur
  l'activité du support comme sur celle des clients.
