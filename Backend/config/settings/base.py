"""Réglages communs à tous les environnements.

La configuration est pilotée par variables d'environnement (django-environ).
Les réglages spécifiques vivent dans dev.py / prod.py.
"""

from pathlib import Path
from urllib.parse import quote

import environ

# Backend/config/settings/base.py -> remonter à Backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-override-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --- Applications -----------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

# Chaque bounded context expose son app Django via sa couche infrastructure.
LOCAL_APPS = [
    "contexts.service_ventes.infrastructure.django_app",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de données --------------------------------------------------------
# PostgreSQL est la base de référence, en dev comme en prod : on ne veut pas
# découvrir en production les différences de comportement de SQLite (types,
# contraintes, transactions).
#
# `DATABASE_URL` reste la source unique de vérité (12-factor) ; à défaut, elle
# est reconstruite depuis les variables DB_* pour rester lisible en local.
DB_USER = env("DB_USER", default="postgres")
DB_PASSWORD = env("DB_PASSWORD", default="")
DB_HOST = env("DB_HOST", default="127.0.0.1")
DB_PORT = env("DB_PORT", default="5432")
DB_NAME = env("DB_NAME", default="siptrack")

# Un mot de passe peut contenir des caractères réservés (@, /, :) : on les encode.
_DEFAULT_DATABASE_URL = (
    f"postgres://{quote(DB_USER, safe='')}:{quote(DB_PASSWORD, safe='')}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

DATABASES = {
    "default": env.db_url("DATABASE_URL", default=_DEFAULT_DATABASE_URL),
}
# Réutiliser la connexion entre requêtes : ouvrir une connexion Postgres coûte
# bien plus cher qu'un fichier SQLite.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# --- Divers -----------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}
