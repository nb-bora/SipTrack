"""Unit of Work basé sur les transactions Django.

Motif « cosmic python » : la transaction est ouverte à l'entrée du bloc ; elle
n'est validée que si commit() a été appelé, sinon elle est annulée.
"""

from __future__ import annotations

from types import TracebackType

from django.db import transaction


class DjangoUnitOfWork:
    def __enter__(self) -> DjangoUnitOfWork:
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self._committed:
            transaction.set_rollback(True)
        self._atomic.__exit__(exc_type, exc, tb)

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        transaction.set_rollback(True)
