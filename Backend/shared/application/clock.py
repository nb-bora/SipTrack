"""Port : Clock (horloge injectable, pour des cas d'usage testables)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...
