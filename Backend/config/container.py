"""Composition Root.

Unique endroit où les adaptateurs concrets (infrastructure) sont branchés sur
les ports du domaine/application. C'est ce qui réalise l'inversion de
dépendances : la couche interface demande un cas d'usage au conteneur sans jamais
connaître l'infrastructure.

Les imports sont différés (dans les méthodes) pour éviter de charger les modèles
ORM avant que les applications Django ne soient prêtes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contexts.catalogue.application.dto import ProduitDTO
    from contexts.catalogue.application.queries import CatalogueQueryService
    from contexts.catalogue.application.use_cases.gerer_le_catalogue import (
        GererLeCatalogueHandler,
    )
    from contexts.catalogue.domain.repositories import ProduitRepository
    from contexts.credit_creances.application.queries import (
        EncoursClientDTO,
        EncoursQueryService,
    )
    from contexts.credit_creances.application.use_cases.accorder_credit import (
        AccorderCreditHandler,
    )
    from contexts.credit_creances.application.use_cases.creer_client import (
        CreerClientHandler,
    )
    from contexts.credit_creances.application.use_cases.enregistrer_remboursement import (
        EnregistrerRemboursementHandler,
    )
    from contexts.credit_creances.domain.repositories import (
        ClientRepository,
        CreditRepository,
        RemboursementRepository,
    )
    from contexts.gouvernance_acces.application.use_cases.gerer_bars import (
        GererBarsHandler,
    )
    from contexts.gouvernance_acces.application.use_cases.gerer_comptes import (
        GererComptesHandler,
    )
    from contexts.gouvernance_acces.application.use_cases.inscrire_utilisateur import (
        InscrireUtilisateurHandler,
    )
    from contexts.gouvernance_acces.domain.repositories import (
        BarRepository,
        CompteRepository,
        ProfilRepository,
    )
    from contexts.service_ventes.application.dto import ServiceDTO
    from contexts.service_ventes.application.ports import (
        OuvertureDeCreance,
        TarifDuProduit,
    )
    from contexts.service_ventes.application.queries import (
        AdditionDetailDTO,
        AdditionQueryService,
        SousCaisseDTO,
        SousCaisseQueryService,
    )
    from contexts.service_ventes.application.use_cases.cloturer_service import (
        CloturerServiceHandler,
    )
    from contexts.service_ventes.application.use_cases.enregistrer_paiement import (
        EnregistrerPaiementHandler,
    )
    from contexts.service_ventes.application.use_cases.enregistrer_vente import (
        EnregistrerVenteHandler,
    )
    from contexts.service_ventes.application.use_cases.ouvrir_addition import (
        OuvrirAdditionHandler,
    )
    from contexts.service_ventes.application.use_cases.ouvrir_service import (
        OuvrirServiceHandler,
    )
    from contexts.service_ventes.application.use_cases.regler_addition import (
        ReglementAdditionHandler,
    )
    from contexts.service_ventes.application.use_cases.verser_recette import (
        VerserRecetteHandler,
    )
    from contexts.service_ventes.domain.repositories import (
        AdditionRepository,
        PaiementRepository,
        ServiceRepository,
        VenteRepository,
        VersementRepository,
    )
    from contexts.stock_inventaire.application.use_cases.gerer_stock import (
        GererStockHandler,
    )
    from contexts.stock_inventaire.domain.repositories import (
        ProduitRepository as StockProduitRepository,
    )
    from shared.application.controle_acces import ControleAcces
    from shared.application.journal import Journal
    from shared.application.journal_acces import JournalDesAcces


class SystemClock:
    """Implémentation par défaut du port Clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class Container:
    """Fabrique de cas d'usage câblés avec l'infrastructure concrète.

    Les adaptateurs **sans état** (repository, journal, horloge) sont créés une
    seule fois puis réutilisés. En revanche, l'Unit of Work est **volontairement
    recréée à chaque cas d'usage** : elle porte l'état d'une transaction et ne
    doit jamais être partagée entre deux exécutions.
    """

    def __init__(self) -> None:
        self._clock = SystemClock()
        self._services: ServiceRepository | None = None
        self._ventes: VenteRepository | None = None
        self._additions: AdditionRepository | None = None
        self._paiements: PaiementRepository | None = None
        self._versements: VersementRepository | None = None
        self._sous_caisses: SousCaisseQueryService | None = None
        self._additions_lecture: AdditionQueryService | None = None
        self._clients: ClientRepository | None = None
        self._credits: CreditRepository | None = None
        self._remboursements: RemboursementRepository | None = None
        self._encours: EncoursQueryService | None = None
        self._produits: ProduitRepository | None = None
        self._bars: BarRepository | None = None
        self._comptes: CompteRepository | None = None
        self._profils: ProfilRepository | None = None
        self._controle_acces: ControleAcces | None = None
        self._acces: JournalDesAcces | None = None
        self._catalogue_lecture: CatalogueQueryService | None = None
        self._produits_stock: StockProduitRepository | None = None
        self._journal: Journal | None = None

    def _service_repository(self) -> ServiceRepository:
        if self._services is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoServiceRepository,
            )

            self._services = DjangoServiceRepository()
        return self._services

    def _vente_repository(self) -> VenteRepository:
        if self._ventes is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoVenteRepository,
            )

            self._ventes = DjangoVenteRepository()
        return self._ventes

    def _addition_repository(self) -> AdditionRepository:
        if self._additions is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoAdditionRepository,
            )

            self._additions = DjangoAdditionRepository()
        return self._additions

    def _paiement_repository(self) -> PaiementRepository:
        if self._paiements is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoPaiementRepository,
            )

            self._paiements = DjangoPaiementRepository()
        return self._paiements

    def _versement_repository(self) -> VersementRepository:
        if self._versements is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoVersementRepository,
            )

            self._versements = DjangoVersementRepository()
        return self._versements

    def _client_repository(self) -> ClientRepository:
        if self._clients is None:
            from contexts.credit_creances.infrastructure.persistence.repository import (
                DjangoClientRepository,
            )

            self._clients = DjangoClientRepository()
        return self._clients

    def _credit_repository(self) -> CreditRepository:
        if self._credits is None:
            from contexts.credit_creances.infrastructure.persistence.repository import (
                DjangoCreditRepository,
            )

            self._credits = DjangoCreditRepository()
        return self._credits

    def _remboursement_repository(self) -> RemboursementRepository:
        if self._remboursements is None:
            from contexts.credit_creances.infrastructure.persistence.repository import (
                DjangoRemboursementRepository,
            )

            self._remboursements = DjangoRemboursementRepository()
        return self._remboursements

    def _encours_query_service(self) -> EncoursQueryService:
        if self._encours is None:
            from contexts.credit_creances.infrastructure.persistence.encours import (
                DjangoEncoursQueryService,
            )

            self._encours = DjangoEncoursQueryService()
        return self._encours

    def _sous_caisse_query_service(self) -> SousCaisseQueryService:
        if self._sous_caisses is None:
            from contexts.service_ventes.infrastructure.persistence.sous_caisse import (
                DjangoSousCaisseQueryService,
            )

            self._sous_caisses = DjangoSousCaisseQueryService()
        return self._sous_caisses

    def _addition_query_service(self) -> AdditionQueryService:
        if self._additions_lecture is None:
            from contexts.service_ventes.infrastructure.persistence.query_service import (
                DjangoAdditionQueryService,
            )

            self._additions_lecture = DjangoAdditionQueryService()
        return self._additions_lecture

    def _produit_repository(self) -> ProduitRepository:
        if self._produits is None:
            from contexts.catalogue.infrastructure.persistence.repository import (
                DjangoProduitRepository,
            )

            self._produits = DjangoProduitRepository()
        return self._produits

    def _bar_repository(self) -> BarRepository:
        if self._bars is None:
            from contexts.gouvernance_acces.infrastructure.persistence.repository import (
                DjangoBarRepository,
            )

            self._bars = DjangoBarRepository()
        return self._bars

    def _compte_repository(self) -> CompteRepository:
        if self._comptes is None:
            from contexts.gouvernance_acces.infrastructure.persistence.repository import (
                DjangoCompteRepository,
            )

            self._comptes = DjangoCompteRepository()
        return self._comptes

    def _profil_repository(self) -> ProfilRepository:
        if self._profils is None:
            from contexts.gouvernance_acces.infrastructure.persistence.repository import (
                DjangoProfilRepository,
            )

            self._profils = DjangoProfilRepository()
        return self._profils

    def _catalogue_query_service(self) -> CatalogueQueryService:
        if self._catalogue_lecture is None:
            from contexts.catalogue.infrastructure.persistence.repository import (
                DjangoCatalogueQueryService,
            )

            self._catalogue_lecture = DjangoCatalogueQueryService()
        return self._catalogue_lecture

    def _tarif_du_produit(self) -> TarifDuProduit:
        """Branche Service & Ventes sur le Catalogue (cf. config/tarifs.py)."""
        from config.tarifs import TarifViaCatalogue

        return TarifViaCatalogue(self._produit_repository())

    def _journal_adapter(self) -> Journal:
        if self._journal is None:
            from shared.infrastructure.journal.adapter import DjangoJournal

            self._journal = DjangoJournal()
        return self._journal

    def ouvrir_service(self) -> OuvrirServiceHandler:
        from contexts.service_ventes.application.use_cases.ouvrir_service import (
            OuvrirServiceHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return OuvrirServiceHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def enregistrer_vente(self) -> EnregistrerVenteHandler:
        from contexts.service_ventes.application.use_cases.enregistrer_vente import (
            EnregistrerVenteHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return EnregistrerVenteHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            ventes=self._vente_repository(),
            additions=self._addition_repository(),
            tarifs=self._tarif_du_produit(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def cloturer_service(self) -> CloturerServiceHandler:
        from contexts.service_ventes.application.use_cases.cloturer_service import (
            CloturerServiceHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return CloturerServiceHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            additions=self._addition_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def ouvrir_addition(self) -> OuvrirAdditionHandler:
        from contexts.service_ventes.application.use_cases.ouvrir_addition import (
            OuvrirAdditionHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return OuvrirAdditionHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            additions=self._addition_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def regler_addition(self) -> ReglementAdditionHandler:
        from contexts.service_ventes.application.use_cases.regler_addition import (
            ReglementAdditionHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return ReglementAdditionHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            additions=self._addition_repository(),
            paiements=self._paiement_repository(),
            ventes=self._vente_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def enregistrer_paiement(self) -> EnregistrerPaiementHandler:
        from contexts.service_ventes.application.use_cases.enregistrer_paiement import (
            EnregistrerPaiementHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return EnregistrerPaiementHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            additions=self._addition_repository(),
            paiements=self._paiement_repository(),
            ventes=self._vente_repository(),
            creances=self._ouverture_de_creance(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def _ouverture_de_creance(self) -> OuvertureDeCreance:
        """Branche Service & Ventes sur Crédit & Créances (cf. config/creances.py)."""
        from config.creances import CreanceViaContexteCredit

        return CreanceViaContexteCredit(self.accorder_credit())

    def verser_recette(self) -> VerserRecetteHandler:
        from contexts.service_ventes.application.use_cases.verser_recette import (
            VerserRecetteHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return VerserRecetteHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            versements=self._versement_repository(),
            paiements=self._paiement_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def sous_caisses_du_service(self, service_id: str) -> tuple[SousCaisseDTO, ...]:
        return self._sous_caisse_query_service().par_service(service_id)

    def addition_detail(self, *, service_id: str, addition_id: str) -> AdditionDetailDTO | None:
        return self._addition_query_service().detail(
            service_id=service_id,
            addition_id=addition_id,
        )

    def service_par_id(self, service_id: str) -> ServiceDTO | None:
        from contexts.service_ventes.application.dto import ServiceDTO

        service = self._service_repository().par_id(service_id)
        return ServiceDTO.depuis(service) if service is not None else None

    def creer_client(self) -> CreerClientHandler:
        from contexts.credit_creances.application.use_cases.creer_client import (
            CreerClientHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return CreerClientHandler(
            uow=DjangoUnitOfWork(),  # fraiche a chaque appel (transaction)
            clients=self._client_repository(),
        )

    def accorder_credit(self) -> AccorderCreditHandler:
        from contexts.credit_creances.application.use_cases.accorder_credit import (
            AccorderCreditHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return AccorderCreditHandler(
            uow=DjangoUnitOfWork(),  # fraiche a chaque appel (transaction)
            clients=self._client_repository(),
            credits=self._credit_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def enregistrer_remboursement(self) -> EnregistrerRemboursementHandler:
        from contexts.credit_creances.application.use_cases.enregistrer_remboursement import (
            EnregistrerRemboursementHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return EnregistrerRemboursementHandler(
            uow=DjangoUnitOfWork(),  # fraiche a chaque appel (transaction)
            credits=self._credit_repository(),
            remboursements=self._remboursement_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def encours_du_client(self, client_id: str) -> EncoursClientDTO | None:
        return self._encours_query_service().par_client(client_id)

    def encours_du_bar(self, bar_id: str) -> tuple[EncoursClientDTO, ...]:
        return self._encours_query_service().tous(bar_id)

    def gerer_le_catalogue(self) -> GererLeCatalogueHandler:
        from contexts.catalogue.application.use_cases.gerer_le_catalogue import (
            GererLeCatalogueHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return GererLeCatalogueHandler(
            uow=DjangoUnitOfWork(),  # fraiche a chaque appel (transaction)
            produits=self._produit_repository(),
            journal=self._journal_adapter(),
        )

    def catalogue_du_bar(self, bar_id: str) -> tuple[ProduitDTO, ...]:
        return self._catalogue_query_service().du_bar(bar_id)

    def gerer_bars(self) -> GererBarsHandler:
        from contexts.gouvernance_acces.application.use_cases.gerer_bars import (
            GererBarsHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return GererBarsHandler(
            uow=DjangoUnitOfWork(),
            bars=self._bar_repository(),
            comptes=self._compte_repository(),
            journal=self._journal_adapter(),
        )

    def inscrire_utilisateur(self) -> InscrireUtilisateurHandler:
        from contexts.gouvernance_acces.application.use_cases.inscrire_utilisateur import (
            InscrireUtilisateurHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return InscrireUtilisateurHandler(
            uow=DjangoUnitOfWork(),
            bars=self._bar_repository(),
            comptes=self._compte_repository(),
            journal=self._journal_adapter(),
        )

    def _journal_des_acces(self) -> JournalDesAcces:
        if self._acces is None:
            from contexts.gouvernance_acces.infrastructure.journal_acces import (
                DjangoJournalDesAcces,
            )

            self._acces = DjangoJournalDesAcces()
        return self._acces

    def acces_du_bar(self, bar_id: str, limite: int = 200) -> list[Any]:
        """Les consultations plateforme d'un bar, de la plus récente à la plus ancienne.

        Bornée : cette liste est faite pour être regardée, pas exportée. L'index
        `(bar_id, -horodatage)` sert exactement cette requête.
        """
        from contexts.gouvernance_acces.infrastructure.django_app.models import (
            AccesPlateformeModel,
        )

        return list(AccesPlateformeModel.objects.filter(bar_id=bar_id)[:limite])

    def controle_acces(self) -> ControleAcces:
        """Le garde que consultent toutes les frontières HTTP.

        Gouvernance est le seul contexte à savoir ce qu'est une capacité ; il
        est donc naturel qu'il réponde. Les autres passent par ce port et ne
        l'importent jamais.
        """
        if self._controle_acces is None:
            from contexts.gouvernance_acces.infrastructure.controle_acces import (
                ControleAccesParCompte,
            )

            self._controle_acces = ControleAccesParCompte(
                self._compte_repository(), self._journal_des_acces()
            )
        return self._controle_acces

    # -- Résolution du bar concerné ---------------------------------------
    #
    # Le garde d'autorisation raisonne toujours sur un bar. Quand l'URL désigne
    # un service, un produit, un client ou un crédit, le bar se lit sur l'objet
    # visé — jamais sur ce que l'appelant en dit. `None` signifie « introuvable ».
    #
    # Ces lectures ne reconstruisent **pas** l'agrégat : elles ne ramènent que la
    # colonne `bar_id`, par la clé primaire. Charger l'objet entier serait du
    # travail perdu — le cas d'usage le rechargera de toute façon juste après, et
    # ce coût se paierait sur *chaque* requête du système.

    @staticmethod
    def _bar_de(modele: type[Any], identifiant: str, colonne: str = "bar_id") -> str | None:
        valeur = modele.objects.filter(pk=identifiant).values_list(colonne, flat=True).first()
        return None if valeur is None else str(valeur)

    def bar_du_service(self, service_id: str) -> str | None:
        from contexts.service_ventes.infrastructure.django_app.models import ServiceModel

        return self._bar_de(ServiceModel, service_id)

    def bar_du_produit_catalogue(self, produit_id: str) -> str | None:
        from contexts.catalogue.infrastructure.django_app.models import ProduitModel

        return self._bar_de(ProduitModel, produit_id)

    def bar_du_produit_stock(self, produit_id: str) -> str | None:
        from contexts.stock_inventaire.infrastructure.django_app.models import (
            ProduitModel as ProduitStockModel,
        )

        return self._bar_de(ProduitStockModel, produit_id, colonne="bar_id")

    def bar_du_client(self, client_id: str) -> str | None:
        from contexts.credit_creances.infrastructure.django_app.models import ClientModel

        return self._bar_de(ClientModel, client_id)

    def bar_du_credit(self, credit_id: str) -> str | None:
        """Un crédit ne porte pas de bar : il tient celui de son débiteur."""
        from contexts.credit_creances.infrastructure.django_app.models import CreditModel

        client_id = self._bar_de(CreditModel, credit_id, colonne="client_id")
        return None if client_id is None else self.bar_du_client(client_id)

    def gerer_comptes(self) -> GererComptesHandler:
        from contexts.gouvernance_acces.application.use_cases.gerer_comptes import (
            GererComptesHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return GererComptesHandler(
            uow=DjangoUnitOfWork(),
            bars=self._bar_repository(),
            comptes=self._compte_repository(),
            profils=self._profil_repository(),
            journal=self._journal_adapter(),
        )

    def doit_changer_mot_de_passe(self, user_id: str) -> bool:
        """Vérifie si l'utilisateur doit changer son mot de passe."""
        return self._profil_repository().doit_changer(user_id)

    def _stock_produit_repository(self) -> StockProduitRepository:
        if self._produits_stock is None:
            from contexts.stock_inventaire.infrastructure.persistence.repository import (
                DjangoProduitRepository,
            )

            self._produits_stock = DjangoProduitRepository()
        return self._produits_stock

    def gerer_stock(self) -> GererStockHandler:
        from contexts.stock_inventaire.application.use_cases.gerer_stock import (
            GererStockHandler,
        )
        from shared.infrastructure.unit_of_work import DjangoUnitOfWork

        return GererStockHandler(
            uow=DjangoUnitOfWork(),
            produits=self._stock_produit_repository(),
            journal=self._journal_adapter(),
        )


container = Container()
