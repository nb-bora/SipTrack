"""Modèles Django du contexte Gouvernance."""

from django.db import models


class BarModel(models.Model):
    """Persistence d'un bar avec son propriétaire."""

    id = models.CharField(max_length=36, primary_key=True)
    nom = models.CharField(max_length=120)
    proprietaire = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="bars_possedes",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gouvernance_bar"
        constraints = [
            models.UniqueConstraint(
                fields=("proprietaire", "nom"),
                name="un_bar_par_nom_et_proprietaire",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nom} (propriétaire: {self.proprietaire.username})"


class CompteModel(models.Model):
    """Persistence d'un compte utilisateur dans un bar."""

    id = models.CharField(max_length=36, primary_key=True)
    bar = models.ForeignKey(BarModel, on_delete=models.CASCADE, related_name="comptes")
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="comptes_gouvernance",
    )
    # Stocke les capacités comme JSON, ou comme ManyToMany ?
    # JSON permet une history immédiate via le journal ; M2M serait plus "Django".
    # Choix : JSON array pour simplicité et cohérence avec l'immutabilité du journal.
    capacites = models.JSONField(default=list)  # ["encaisser", "cloturer_service", ...]
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gouvernance_compte"
        constraints = [
            models.UniqueConstraint(
                fields=("bar", "user"),
                name="un_compte_par_user_et_bar",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.bar.nom} ({len(self.capacites)} capacités)"
