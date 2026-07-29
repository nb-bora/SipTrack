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


class AdministrateurPlateformeModel(models.Model):
    """Un compte agissant au-dessus des bars : support, exploitation, facturation.

    Rattaché à un utilisateur, jamais à un bar — c'est ce qui le distingue d'un
    `CompteModel`. Les deux peuvent coexister pour la même personne : elle tient
    alors ses droits d'exploitation de son compte de bar, et rien d'autre.
    """

    id = models.CharField(max_length=36, primary_key=True)
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="administration_plateforme",
    )
    capacites = models.JSONField(default=list)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gouvernance_administrateur_plateforme"

    def __str__(self) -> str:
        etat = "actif" if self.actif else "suspendu"
        return f"{self.user.username} — plateforme ({etat})"


class AccesPlateformeModel(models.Model):
    """Trace d'une consultation faite au titre du privilège plateforme.

    Table séparée du journal métier, à dessein : ce dernier prend un verrou
    global pour chaîner ses empreintes, et une consultation n'est pas un Fait
    d'exploitation. Ici, une insertion simple, indexée sur le bar — la question
    posée est toujours « qui a regardé *mon* bar ».

    Consultable par le propriétaire du bar. C'est la contrepartie qui rend le
    privilège de lecture acceptable.
    """

    id = models.CharField(max_length=36, primary_key=True)
    administrateur_id = models.CharField(max_length=36)
    bar_id = models.CharField(max_length=36)
    operation = models.CharField(max_length=120)
    horodatage = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gouvernance_acces_plateforme"
        ordering = ["-horodatage"]
        indexes = [
            # « Qui a consulté mon bar, du plus récent au plus ancien. »
            models.Index(fields=["bar_id", "-horodatage"], name="acces_par_bar_et_date"),
        ]

    def __str__(self) -> str:
        return f"{self.administrateur_id} → {self.bar_id} ({self.operation})"
