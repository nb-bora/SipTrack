"""Bounded context « Gouvernance & Accès ».

**Amorce délibérément minimale.** Ce contexte n'expose aujourd'hui qu'une couche
interface : l'obtention d'un jeton. Il n'a ni domaine ni application, parce que
l'authentification n'est pas une règle métier — c'est un service technique.

Ce qui relève vraiment de ce contexte reste à construire : acteurs, capacités,
délégation à trois niveaux (réservé / sous politique / pleinement délégué) et
validations, tels que décrits dans `docs/02-modele-metier.md` §3.
"""
