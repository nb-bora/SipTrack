"""Réglages de développement."""

# L'import générique est la convention Django pour les settings : un fichier
# d'environnement hérite de la base et n'en surcharge que ce qui diffère.
# Énumérer les noms reviendrait à maintenir une liste qui se périmerait
# silencieusement à chaque réglage ajouté.
from .base import *  # noqa: F403  # NOSONAR

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104
