"""Réglages de production.

La base (Postgres) et les secrets viennent de l'environnement (DATABASE_URL,
SECRET_KEY). Aucun secret en dur.
"""

import os

# Import générique : convention Django pour les settings (cf. dev.py).
from .base import *  # noqa: F403  # NOSONAR
from .base import MIDDLEWARE
from .garde import exiger

DEBUG = False


# Jamais `env(..., default=...)` ici : le défaut est précisément le danger.
SECRET_KEY = exiger("SECRET_KEY")

# On relit la variable brute au lieu de passer par `env` : le schéma déclaré
# dans base.py porte le défaut de développement (localhost, 127.0.0.1), qui
# n'a rien à faire ici. En production la liste vaut exactement ce qui est
# déclaré, plus l'hôte que Render publie de lui-même.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]

_hote_render = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if _hote_render:
    ALLOWED_HOSTS.append(_hote_render)
    # Django exige l'origine complète, schéma compris, pour le contrôle CSRF.
    CSRF_TRUSTED_ORIGINS = [f"https://{_hote_render}"]

# WhiteNoise sert les fichiers statiques depuis le processus applicatif. Sur
# Render il n'y a pas de nginx devant : sans lui, l'admin Django et l'interface
# Swagger arriveraient sans CSS.
MIDDLEWARE = [
    MIDDLEWARE[0],  # SecurityMiddleware reste en tête
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Empreinte dans le nom de fichier + compression : le cache du navigateur
    # peut être agressif sans jamais servir une version périmée.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Durcissement HTTP (dérrière un reverse-proxy TLS).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
