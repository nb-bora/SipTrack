"""Réglages de production.

La base (Postgres) et les secrets viennent de l'environnement (DATABASE_URL,
SECRET_KEY). Aucun secret en dur.
"""

# Import générique : convention Django pour les settings (cf. dev.py).
from .base import *  # noqa: F403  # NOSONAR

DEBUG = False

# Durcissement HTTP (dérrière un reverse-proxy TLS).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
