"""Réglages de développement."""

# L'import générique est la convention Django pour les settings : un fichier
# d'environnement hérite de la base et n'en surcharge que ce qui diffère.
# Énumérer les noms reviendrait à maintenir une liste qui se périmerait
# silencieusement à chaque réglage ajouté.
from corsheaders.defaults import default_headers

from .base import *  # noqa: F403  # NOSONAR

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104

# --- CORS -------------------------------------------------------------------
# Toutes les origines sont acceptées **en développement seulement**. Le poste de
# dev sert l'app tantôt sur localhost, tantôt sur l'IP du réseau local quand on
# teste depuis un téléphone : énumérer ces origines reviendrait à maintenir une
# liste qui se périme à chaque changement de réseau.
#
# Ce réglage vit ici et nulle part ailleurs. Le mettre dans base.py le ferait
# hériter par prod.py, et une API qui accepte toute origine sur Internet laisse
# n'importe quel site déclencher des appels au nom de la personne connectée.
CORS_ALLOW_ALL_ORIGINS = True

# L'en-tête d'idempotence n'est pas dans la liste par défaut de django-cors-
# headers. Sans cette ligne, le preflight d'une écriture serait refusé : les
# lectures passeraient, toute vente échouerait — et la panne semblerait venir du
# métier plutôt que du transport.
CORS_ALLOW_HEADERS = [*default_headers, "idempotency-key"]

# Un rejeu est signalé par cet en-tête de réponse. Le navigateur ne l'expose au
# JavaScript que s'il est déclaré ici ; sinon le client ne peut pas distinguer
# une écriture neuve d'un rejeu servi de mémoire.
CORS_EXPOSE_HEADERS = ["Idempotency-Replayed"]
