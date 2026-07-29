#!/usr/bin/env bash
# Étape de build Render. Exécutée depuis Backend/ (cf. rootDir dans render.yaml).
#
# `set -euo pipefail` : la moindre commande en échec arrête le build. Sans lui,
# un collectstatic raté passerait inaperçu et l'application partirait en ligne
# sans ses fichiers statiques.
set -euo pipefail

# La version est figée pour que le build soit reproductible — même logique que
# le lockfile : deux déploiements du même commit installent les mêmes octets.
UV_VERSION="0.11.21"

echo "--> Installation de uv ${UV_VERSION}"
# --only-binary :all: : uniquement des roues déjà construites. Sans ce garde-fou,
# pip accepterait une distribution source, dont le script d'installation
# s'exécuterait avec les droits du build — et le build a accès à DATABASE_URL.
pip install --quiet --only-binary :all: "uv==${UV_VERSION}"

echo "--> Dépendances (lockfile figé, sans les outils de développement)"
# --no-build : même garde-fou côté uv, pour les mêmes raisons.
uv sync --locked --no-dev --no-build

echo "--> Fichiers statiques"
uv run --frozen --no-dev --no-build python manage.py collectstatic --no-input

echo "--> Migrations"
uv run --frozen --no-dev --no-build python manage.py migrate --no-input

echo "--> Build terminé"
