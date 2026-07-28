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
pip install --quiet "uv==${UV_VERSION}"

echo "--> Dépendances (lockfile figé, sans les outils de développement)"
# --no-build : uniquement des roues déjà construites, donc aucun script
# d'installation d'une dépendance ne s'exécute pendant le build.
uv sync --locked --no-dev --no-build

echo "--> Fichiers statiques"
uv run --frozen --no-dev python manage.py collectstatic --no-input

echo "--> Migrations"
uv run --frozen --no-dev python manage.py migrate --no-input

echo "--> Build terminé"
