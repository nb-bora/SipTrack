"""Exiger qu'un réglage soit fourni, plutôt que de se rabattre sur un défaut.

Vit dans son propre module, et non dans `prod.py`, pour une raison précise :
`prod.py` **appelle** ce garde au chargement. L'importer pour en éprouver le
comportement déclencherait donc le garde lui-même, et le test ne pourrait
s'exécuter que dans un environnement… déjà correctement configuré — c'est-à-dire
jamais là où il servirait.

Une fonction sans effet de bord se teste ; un module qui en a se contente
d'être exécuté.
"""

from __future__ import annotations

import os


class ConfigurationManquante(RuntimeError):
    """Un réglage indispensable est absent : mieux vaut ne pas démarrer."""


def exiger(nom: str) -> str:
    """Lit une variable d'environnement, ou refuse de démarrer.

    `base.py` porte des valeurs de repli pour le développement. En production,
    hériter de l'un de ces replis serait pire qu'une panne : l'application
    démarrerait, servirait, et signerait jetons et cookies avec une clé
    **publiée dans un dépôt public**.

    Une panne au démarrage se voit dans les journaux. Une clé de repli qui sert
    silencieusement, non.
    """
    valeur = os.environ.get(nom, "").strip()
    if not valeur:
        raise ConfigurationManquante(
            f"{nom} est absent de l'environnement. La production ne démarre pas "
            f"sans — voir docs/06-deploiement.md."
        )
    return valeur
