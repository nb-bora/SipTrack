"""Cas d'usage : encaisser un paiement sur une addition.

Le règlement d'une addition est une **conséquence**, pas une déclaration :
quand le cumul des paiements couvre le total consommé, l'addition passe d'
elle-même à REGLEE. C'est ce qui empêche de clore une table sans avoir encaissé.

Le crédit est une forme de paiement à part : il solde l'addition sans qu'aucun
argent n'entre. Ce qui entre à la place, c'est une **dette au nom de quelqu'un**
— sans quoi la consommation s'évaporerait du décompte.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import (
    EnregistrerPaiementCommand,
    PaiementDTO,
)
from contexts.service_ventes.application.ports import OuvertureDeCreance
from contexts.service_ventes.domain.enums import FormePaiement
from contexts.service_ventes.domain.exceptions import (
    AdditionIntrouvable,
    ClientRequisPourUnCredit,
    PaiementSuperieurAuReste,
)
from contexts.service_ventes.domain.paiement import Paiement
from contexts.service_ventes.domain.repositories import (
    AdditionRepository,
    PaiementRepository,
    VenteRepository,
)
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class EnregistrerPaiementHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        additions: AdditionRepository,
        paiements: PaiementRepository,
        ventes: VenteRepository,
        creances: OuvertureDeCreance,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._additions = additions
        self._paiements = paiements
        self._ventes = ventes
        self._creances = creances
        self._journal = journal
        self._clock = clock

    def executer(self, commande: EnregistrerPaiementCommand) -> PaiementDTO:
        with self._uow:
            addition = self._additions.par_id(commande.addition_id)
            # Une addition d'un autre service est, d'ici, inexistante.
            if addition is None or addition.service_id != commande.service_id:
                raise AdditionIntrouvable(commande.addition_id)
            addition.accepter_consommation()  # même règle : elle doit être ouverte

            forme = FormePaiement(commande.forme_paiement)
            if forme is FormePaiement.CREDIT and not commande.client_id:
                raise ClientRequisPourUnCredit(addition.id)

            reste = self._reste_a_payer(addition.id)
            if commande.montant > reste:
                raise PaiementSuperieurAuReste(addition.id, reste)

            horodatage = self._clock.now()
            paiement = Paiement.encaisser(
                addition_id=addition.id,
                service_id=addition.service_id,
                montant=Montant(commande.montant),
                forme_paiement=forme,
                horodatage=horodatage,
                auteur_id=commande.auteur_id,
            )
            self._paiements.ajouter(paiement)

            # La dette naît dans la même transaction que le paiement qui la crée :
            # il ne peut pas exister de crédit encaissé sans créance en face.
            if forme is FormePaiement.CREDIT:
                self._creances.ouvrir(
                    client_id=commande.client_id,
                    service_id=addition.service_id,
                    addition_id=addition.id,
                    montant=commande.montant,
                    auteur_id=commande.auteur_id,
                )

            evenements = list(paiement.evenements_non_publies())

            # Soldée : l'addition se règle d'elle-même, dans la même transaction.
            # Le crédit règle l'addition comme les autres formes : la table est
            # libérée, la consommation est comptée, et c'est la créance — pas
            # l'addition — qui reste ouverte jusqu'au remboursement.
            if commande.montant == reste:
                addition.regler(auteur_id=commande.auteur_id, horodatage=horodatage)
                self._additions.mettre_a_jour(addition)
                evenements.extend(addition.evenements_non_publies())

            self._journal.enregistrer(evenements, auteur_id=commande.auteur_id)
            paiement.purger_evenements()
            addition.purger_evenements()
            self._uow.commit()
            return PaiementDTO.depuis(paiement, reste_a_payer=reste - commande.montant)

    def _reste_a_payer(self, addition_id: str) -> int:
        du = self._ventes.total_addition(addition_id)
        encaisse = self._paiements.total_encaisse(addition_id)
        return du - encaisse
