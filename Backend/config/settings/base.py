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
    "rest_framework.authtoken",
    "drf_spectacular",
    # Sert les assets de Swagger depuis le serveur, pas depuis un CDN : l'outil
    # vise des bars, pas un bureau fibré.
    "drf_spectacular_sidecar",
]

# Le journal est transverse : tous les contextes y écrivent, aucun ne le possède.
LOCAL_APPS = [
    "shared.infrastructure.journal",
    "shared.infrastructure.observabilite",
    "shared.infrastructure.idempotence",
    # Chaque bounded context expose son app Django via sa couche infrastructure.
    "contexts.service_ventes.infrastructure.django_app",
    "contexts.credit_creances.infrastructure.django_app",
    "contexts.catalogue.infrastructure.django_app",
    "contexts.gouvernance_acces.infrastructure.django_app",
    "contexts.stock_inventaire.infrastructure.django_app",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Placé tôt : il mesure la durée réellement subie par l'appelant, en
    # englobant le travail des middlewares suivants. Mais après la sécurité, qui
    # doit pouvoir refuser avant qu'on ne mesure quoi que ce soit.
    "shared.infrastructure.observabilite.middleware.ObservabiliteMiddleware",
    # Après l'observabilité, pour qu'un rejeu apparaisse dans les logs comme
    # n'importe quelle requête — c'est ainsi qu'on verra un client qui rejoue en
    # boucle. Avant tout le reste, pour ne pas exécuter la vue deux fois.
    "shared.infrastructure.idempotence.middleware.IdempotenceMiddleware",
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
# Cible de `collectstatic`. Nécessaire dès qu'un serveur autre que celui de
# développement sert les fichiers (admin Django, assets Swagger embarqués).
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # Jeton plutôt que session : l'app mobile est offline-first, elle ne peut
    # pas dépendre d'une session serveur ni d'un cycle de rafraîchissement.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    # Fermé par défaut : une route nouvellement ajoutée est protégée sans que
    # personne ait à y penser. C'est l'inverse qui serait dangereux.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Freine le bourrinage de mots de passe sur l'obtention de jeton.
        "obtention_jeton": env("THROTTLE_OBTENTION_JETON", default="10/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --- Documentation OpenAPI --------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "SipTrack — API",
    "DESCRIPTION": (
        "Le registre incontestable du bar.\n\n"
        "Toutes les routes exigent un jeton : `Authorization: Token <jeton>`. "
        "L'obtenir via `POST /api/auth/jeton/`, puis le coller dans « Authorize ».\n\n"
        "L'auteur d'un Fait est toujours déduit du compte authentifié — jamais "
        "du corps de la requête."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}


# Nombre de pannes conservées en base. Réglable sans redéploiement : c'est le
# curseur qu'on veut pouvoir baisser pendant l'incident, pas après.
OBSERVABILITE_ERREURS_MAX = env.int("OBSERVABILITE_ERREURS_MAX", default=5_000)

# Nombre de clés d'idempotence conservées. Une clé couvre un rejeu qui suit de
# près la requête d'origine : la mémoire n'a pas à être longue.
IDEMPOTENCE_CLES_MAX = env.int("IDEMPOTENCE_CLES_MAX", default=20_000)


# ---------------------------------------------------------------------------
# Journalisation technique
#
# Distincte du journal des Mouvements : celui-ci consigne des Faits métier,
# chaînés et opposables ; ceci sert à comprendre une panne. Les confondre
# affaiblirait le premier.
#
# Sortie standard uniquement : Render l'agrège. Écrire dans un fichier sur un
# système de fichiers éphémère donnerait des logs qui disparaissent au
# redéploiement — exactement quand on en a besoin.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shared.infrastructure.observabilite.journalisation.FormatteurJSON",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("NIVEAU_LOG", default="INFO"),
    },
    "loggers": {
        # Le journal d'accès de Django double la ligne que produit notre
        # middleware, sans l'auteur ni la corrélation. On garde la nôtre.
        "django.server": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # `django.request` émet un WARNING pour chaque 4xx. Un client qui envoie
        # n'importe quoi n'est pas un incident : le bruit masquerait les vraies
        # pannes, que notre middleware relève déjà en ERROR.
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
