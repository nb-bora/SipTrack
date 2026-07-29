"""Ce qui a cassé, avec de quoi comprendre pourquoi.

**Distinct du journal des Mouvements**, et il faut que cela le reste. Le journal
métier consigne des Faits d'exploitation, chaînés par empreinte, sous verrou
global : sa force vient de son étroitesse. Une pile d'appels Python n'y a pas sa
place, et l'y verser ferait croître le coût de vérification de la chaîne pour
rien.

Ce qui n'est **pas** enregistré ici, délibérément : le corps des requêtes et des
réponses. Il contient des noms de clients, des dettes, des montants. En garder
une copie créerait un second exemplaire des données sensibles, moins bien
protégé que l'original — un passif, pas un actif.
"""

from __future__ import annotations

from django.db import models

# Valeur de repli. La borne réelle vient de `settings.OBSERVABILITE_ERREURS_MAX`
# — c'est un curseur d'exploitation : le jour où une boucle d'erreurs remplit la
# table, on doit pouvoir le baisser sans redéployer.
LIGNES_CONSERVEES_PAR_DEFAUT = 5_000


class ErreurTechnique(models.Model):
    """Une requête qui s'est terminée en 5xx.

    Les 4xx n'y figurent pas : un client qui envoie n'importe quoi n'est pas un
    incident, et les enregistrer noierait les vraies pannes.
    """

    id = models.BigAutoField(primary_key=True)
    # Reliure avec les logs : la même valeur voyage dans l'en-tête de réponse et
    # dans chaque ligne de log de la requête.
    correlation_id = models.CharField(max_length=36, db_index=True)
    horodatage = models.DateTimeField(auto_now_add=True, db_index=True)
    methode = models.CharField(max_length=10)
    chemin = models.CharField(max_length=255)
    statut = models.PositiveSmallIntegerField()
    # Qui subissait la panne — pour rappeler la bonne personne, pas pour la juger.
    auteur_id = models.CharField(max_length=36, blank=True, default="")
    exception = models.CharField(max_length=255, blank=True, default="")
    trace = models.TextField(blank=True, default="")

    class Meta:
        db_table = "observabilite_erreur"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.statut} {self.methode} {self.chemin}"
