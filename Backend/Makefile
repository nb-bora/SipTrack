# Raccourcis de développement. Usage : make <cible>
.PHONY: install migrate run test lint format typecheck arch check

install:
	uv sync

migrate:
	uv run manage.py migrate

run:
	uv run manage.py runserver

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

arch:
	uv run lint-imports

# Vérification complète (à lancer avant de pousser)
check: lint typecheck arch test
