"""Mémoire des écritures déjà traitées.

Une serveuse peut légitimement saisir deux fois la même bière au même prix : le
contenu d'une requête ne dit donc pas si c'est un doublon. Seule une clé fournie
par le client distingue « deux consommations » de « deux fois la même requête ».
"""

from __future__ import annotations

from django.db import models

# Au-delà, les plus anciennes clés cèdent la place. Une clé sert à couvrir un
# rejeu qui suit de près la requête d'origine — un client hors ligne depuis des
# semaines a d'autres problèmes que celui-ci.
CLES_CONSERVEES_PAR_DEFAUT = 20_000


class RequeteIdempotente(models.Model):
    """Une écriture identifiée par la clé que son auteur lui a donnée.

    L'unicité porte sur **(porteur, clé)** et non sur la clé seule : deux clients
    qui choisiraient la même valeur ne doivent ni se gêner, ni pouvoir lire la
    réponse l'un de l'autre. Le porteur est une empreinte du jeton — jamais le
    jeton lui-même.
    """

    EN_COURS = "en_cours"
    TERMINEE = "terminee"

    id = models.BigAutoField(primary_key=True)
    porteur = models.CharField(max_length=64)
    cle = models.CharField(max_length=200)
    # Empreinte de la requête : même clé + corps différent = la clé ne désigne
    # pas cette requête-là, et rendre la réponse mémorisée serait un mensonge.
    empreinte = models.CharField(max_length=64)
    statut = models.CharField(max_length=10, default=EN_COURS)
    code_http = models.PositiveSmallIntegerField(null=True, blank=True)
    corps = models.BinaryField(null=True, blank=True)
    type_contenu = models.CharField(max_length=100, blank=True, default="")
    horodatage = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "idempotence_requete"
        constraints = [
            models.UniqueConstraint(fields=("porteur", "cle"), name="une_cle_par_porteur"),
        ]

    def __str__(self) -> str:
        return f"{self.cle} ({self.statut})"
