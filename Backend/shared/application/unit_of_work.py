"""Port : Unit of Work.

Représente une transaction atomique : un cas d'usage réussit ou échoue en bloc.
L'implémentation concrète vit dans la couche infrastructure.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol


class UnitOfWork(Protocol):
    def __enter__(self) -> UnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
