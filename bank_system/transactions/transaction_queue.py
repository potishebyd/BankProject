from datetime import datetime

from ..core.enums import TransactionStatus
from ..core.exceptions import InvalidOperationError, TransactionNotFoundError
from .transaction import Transaction


class TransactionQueue:
    _QUEUED_STATUSES = (
        TransactionStatus.pending,
        TransactionStatus.deferred,
        TransactionStatus.retry,
    )

    def __init__(self):
        self._items: list[Transaction] = []

    def __len__(self):
        return len(self._items)

    @property
    def transactions(self):
        return list(self._items)

    def add(
        self,
        transaction: Transaction,
        priority: int = 0,
        scheduled_at=None,
    ):
        if not isinstance(transaction, Transaction):
            raise InvalidOperationError("Incorrect transaction")

        if transaction.status not in self._QUEUED_STATUSES:
            raise InvalidOperationError("Transaction cannot be queued")

        if any(
            item.transaction_id == transaction.transaction_id for item in self._items
        ):
            raise InvalidOperationError("Transaction is already queued")

        if transaction.status != TransactionStatus.retry:
            transaction.assign_queue_meta(priority, scheduled_at)

        self._items.append(transaction)
        return transaction

    def cancel(self, transaction_id: str, now=None):
        if not isinstance(transaction_id, str) or not transaction_id:
            raise ValueError("Incorrect transaction id")

        for transaction in self._items:
            if transaction.transaction_id == transaction_id:
                transaction.mark_cancelled(
                    "Cancelled by client",
                    now or datetime.now(),
                )
                self._items.remove(transaction)
                return transaction

        raise TransactionNotFoundError("Transaction not found")

    def pop_ready(self, now):
        ready = [item for item in self._items if self._is_ready(item, now)]
        if not ready:
            return None

        ready.sort(key=lambda item: (-item.priority, item.created_at, item.sequence))
        chosen = ready[0]
        self._items.remove(chosen)
        return chosen

    @staticmethod
    def _is_ready(transaction: Transaction, now) -> bool:
        if transaction.status not in (
            TransactionStatus.pending,
            TransactionStatus.deferred,
            TransactionStatus.retry,
        ):
            return False

        if transaction.scheduled_at is not None and transaction.scheduled_at > now:
            return False

        return True
