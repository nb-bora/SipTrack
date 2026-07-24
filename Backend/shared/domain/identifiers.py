"""Génération d'identifiants du domaine (indépendante de toute technologie)."""

from __future__ import annotations

import uuid


def new_id() -> str:
    """Retourne un identifiant unique sous forme de chaîne (UUID4)."""
    return str(uuid.uuid4())
