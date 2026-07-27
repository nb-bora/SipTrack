# SipTrack

[![CI](https://github.com/nb-bora/SipTrack/workflows/CI/badge.svg)](https://github.com/nb-bora/SipTrack/actions?query=workflow:CI)

> Le registre incontestable du bar.

**SipTrack** est un outil de **gestion et d'audit** pour bars au Cameroun : il trace chaque
mouvement de stock, d'argent, de vidanges, de casiers et de créances, de façon **vérifiable et
attribuable** — même hors ligne, même quand le propriétaire n'est pas là.

## Structure du dépôt

| Dossier | Rôle |
|---|---|
| [`Backend/`](./Backend/) | API (Django, DDD + Clean Architecture) |
| [`Frontend/`](./Frontend/) | Application web |
| [`Mobile/`](./Mobile/) | Application mobile (offline-first) |
| [`docs/`](./docs/) | **Documentation de référence** : métier, langage commun, architecture, décisions (ADR) |

## Par où commencer

👉 Lire d'abord la [documentation de référence](./docs/README.md) : elle fige le modèle métier
et l'architecture, et sert de **contrat partagé** par les trois briques du projet.

## Principes fondateurs

1. **La confiance ne se décrète pas, elle se prouve** — on rend les faits incontestables,
   et personne n'échappe au journal.
2. **Le journal des mouvements est la seule vérité** — tous les états sont calculés.
3. **La personne honnête est protégée** autant que le propriétaire est renseigné.
