"""Le journal des Mouvements — service transverse, pas un bounded context.

Tous les contextes écrivent leurs Faits ici : c'est la seule vérité du produit,
tous les états (stock, caisse, créances) s'en déduisent. Le journal ne peut donc
appartenir à aucun contexte en particulier, sous peine d'obliger les suivants à
le dupliquer ou à violer l'isolation (ADR-0005).

Le port est déclaré dans `shared/application/journal.py` ; ceci en est
l'implémentation Django.
"""
