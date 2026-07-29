# ADR-0008 — Observer ce qui casse, sans copier ce qui est sensible

**Statut** : accepté — 2026-07-29

## La demande, et la confusion qu'elle contient

« Un module d'observabilité qui traque tout ce qui se passe sur le système. »

Deux objets de nature **opposée** se cachent derrière ce « tout » :

| | Journal des Mouvements | Observabilité technique |
|---|---|---|
| Contenu | Faits d'exploitation | Requêtes, pannes, durées |
| Propriété | Opposable, chaîné, immuable | Jetable, borné |
| Volume | ~200 par soirée | Des milliers par jour |
| Sert à | Prouver | Comprendre |

Les confondre affaiblirait le premier. Le journal métier tire sa force de son
**étroitesse** : on peut vérifier la chaîne entière parce qu'elle ne contient que
des Faits. Y verser les logs HTTP ferait croître le coût de vérification pour
rien.

Et il y a un obstacle dirimant : `DjangoJournal.enregistrer` prend un **verrou
global à toute la plateforme** pour garantir le chaînage — son commentaire dit
qu'il sérialise « deux bars, deux serveuses ». Une ligne de log par requête y
aurait sérialisé l'API entière.

## La décision

### Ce qui est observé

- **Un identifiant de corrélation** par requête, rendu dans l'en-tête
  `X-Correlation-Id`. C'est lui qui relie « ça a planté vers 21 h » aux lignes
  de log. S'il est fourni par l'appelant, il est conservé : un appel se suit
  alors du terminal jusqu'ici.
- **Une ligne JSON par requête** : méthode, chemin, statut, durée, auteur.
  Du texte libre se cherche à l'œil ; du JSON se filtre.
- **Les 5xx en base**, avec leur trace. Les 4xx non : un client qui envoie
  n'importe quoi n'est pas un incident, et les enregistrer noierait les vraies
  pannes.

### Ce qui n'est pas observé, délibérément

**Le corps des requêtes et des réponses.** Il porte des noms de clients, des
dettes, des montants. En garder une copie créerait un **second exemplaire des
données sensibles, moins bien protégé que l'original** — un passif, pas un actif.
`test_aucun_corps_de_requete_ne_part_dans_les_logs` interdit la régression.

**Le nom d'utilisateur.** On journalise la clé technique : renommer un compte ne
doit pas rendre illisibles les logs déjà écrits. Même raison que dans le journal
métier.

### Le volume est borné, et le curseur est réglable à chaud

La base est partagée avec les données du produit. **Un module qui observe ne doit
pas pouvoir faire tomber ce qu'il observe** — et une boucle d'erreurs est
précisément le moment où ce garde sert.

La table des pannes est plafonnée par comparaison à la plus grande clé primaire,
jamais par `COUNT(*)` : compter coûte un parcours, comparer coûte un index, et la
différence compte exactement quand la table se remplit vite.

`OBSERVABILITE_ERREURS_MAX` vient de l'environnement. C'est le curseur qu'on veut
pouvoir baisser **pendant** l'incident, pas après.

### Rien ne fait échouer la requête observée

Si la base est ce qui est cassé, l'écriture de la panne échoue aussi. Elle est
capturée et journalisée en `error` : une erreur ne doit pas en devenir deux.

## Ce qui a été écarté

**Écrire les logs dans un fichier.** Le système de fichiers de Render est
éphémère : les logs disparaîtraient au redéploiement, c'est-à-dire exactement
quand on en a besoin. Sortie standard uniquement, que Render agrège.

**Laisser `django.request` émettre un WARNING par 4xx.** Le bruit aurait masqué
les vraies pannes, que le middleware relève déjà en `ERROR`.

**Un service externe (Sentry, Datadog).** Meilleur outil, mais une dépendance
payante et une sortie de données hors du pays. À reconsidérer si le volume le
justifie.

## Ce que cela ne couvre pas

- **Pas de métriques agrégées** (taux d'erreur, percentiles de latence). Les
  durées sont dans les logs ; les agréger demande un outil qu'on n'a pas.
- **Pas d'alerte.** Personne n'est prévenu automatiquement d'une panne.
- **Pas de traçage distribué.** Un seul service pour l'instant ; l'identifiant de
  corrélation est déjà en place le jour où il y en aura deux.
