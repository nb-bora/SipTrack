"""Énumérations du domaine Service & Ventes."""

from __future__ import annotations

from enum import StrEnum


class StatutService(StrEnum):
    OUVERT = "ouvert"
    CLOTURE = "cloture"
    SCELLE = "scelle"


class FormePaiement(StrEnum):
    ESPECES = "especes"
    MOBILE_MONEY = "mobile_money"
    CREDIT = "credit"
