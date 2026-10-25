import uuid
from datetime import datetime

from ..accounts.bank_account import BankAccount
from ..core.enums import Currency, TransactionStatus, TransactionType
from ..core.exceptions import InvalidOperationError


class Transaction:
    _sequence = 0

    def __init__(
        self,
        transaction_type: TransactionType,
        amount: int | float,
        currency: Currency,
        sender: BankAccount | None = None,
        recipient: BankAccount | None = None,
        external_recipient: str | None = None,
        transaction_id: str | None = None,
        created_at: datetime | None = None,
    ):
        if not isinstance(transaction_type, TransactionType):
            raise ValueError("Incorrect transaction type")

        BankAccount._validate_amount(amount, "Incorrect transaction amount")
        if amount == 0:
            raise InvalidOperationError("Transaction amount must be positive")

        if not isinstance(currency, Currency):
            raise ValueError("Incorrect currency")

        if transaction_id is not None:
            if not isinstance(transaction_id, str) or not transaction_id:
                raise ValueError("Incorrect transaction id")

        if created_at is None:
            created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            raise ValueError("Incorrect created time")

        self._validate_parties(
            transaction_type, sender, recipient, external_recipient
        )

        Transaction._sequence += 1
        self._sequence = Transaction._sequence
        self._transaction_id = transaction_id or uuid.uuid4().hex[:8]
        self._type = transaction_type
        self._amount = amount
        self._currency = currency
        self._commission = 0
        self._converted_amount = None
        self._sender = sender
        self._recipient = recipient
        self._external_recipient = external_recipient
        self._status = TransactionStatus.pending
        self._rejection_reason = None
        self._priority = 0
        self._attempts = 0
        self._created_at = created_at
        self._scheduled_at = None
        self._processed_at = None
        self._completed_at = None

    @staticmethod
    def _validate_parties(transaction_type, sender, recipient, external_recipient):
        if sender is not None and not isinstance(sender, BankAccount):
            raise ValueError("Incorrect sender")

        if recipient is not None and not isinstance(recipient, BankAccount):
            raise ValueError("Incorrect recipient")

        if external_recipient is not None:
            if not isinstance(external_recipient, str) or not external_recipient.strip():
                raise ValueError("Incorrect external recipient")

        if transaction_type == TransactionType.deposit:
            if recipient is None or sender is not None or external_recipient is not None:
                raise InvalidOperationError("Deposit requires only a recipient")

        elif transaction_type == TransactionType.withdraw:
            if sender is None or recipient is not None or external_recipient is not None:
                raise InvalidOperationError("Withdraw requires only a sender")

        elif transaction_type == TransactionType.transfer:
            if sender is None or recipient is None or external_recipient is not None:
                raise InvalidOperationError("Transfer requires sender and recipient")
            if sender is recipient:
                raise InvalidOperationError("Sender and recipient must differ")

        elif transaction_type == TransactionType.external:
            if sender is None or recipient is not None or external_recipient is None:
                raise InvalidOperationError(
                    "External transfer requires sender and external recipient"
                )

    @property
    def transaction_id(self):
        return self._transaction_id

    @property
    def type(self):
        return self._type

    @property
    def amount(self):
        return self._amount

    @property
    def currency(self):
        return self._currency

    @property
    def commission(self):
        return self._commission

    @property
    def converted_amount(self):
        return self._converted_amount

    @property
    def sender(self):
        return self._sender

    @property
    def recipient(self):
        return self._recipient

    @property
    def external_recipient(self):
        return self._external_recipient

    @property
    def status(self):
        return self._status

    @property
    def rejection_reason(self):
        return self._rejection_reason

    @property
    def priority(self):
        return self._priority

    @property
    def attempts(self):
        return self._attempts

    @property
    def sequence(self):
        return self._sequence

    @property
    def created_at(self):
        return self._created_at

    @property
    def scheduled_at(self):
        return self._scheduled_at

    @property
    def processed_at(self):
        return self._processed_at

    @property
    def completed_at(self):
        return self._completed_at

    def assign_queue_meta(self, priority: int, scheduled_at: datetime | None = None):
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ValueError("Incorrect priority")

        self._priority = priority

        if scheduled_at is None:
            return

        if not isinstance(scheduled_at, datetime):
            raise ValueError("Incorrect scheduled time")

        self._scheduled_at = scheduled_at
        self._status = TransactionStatus.deferred

    def mark_processing(self, now: datetime):
        self._status = TransactionStatus.processing
        self._processed_at = now
        self._attempts += 1

    def mark_completed(self, now: datetime, commission: int | float, converted_amount):
        self._commission = commission
        self._converted_amount = converted_amount
        self._status = TransactionStatus.completed
        self._rejection_reason = None
        self._completed_at = now

    def mark_retry(self, reason: str):
        self._status = TransactionStatus.retry
        self._rejection_reason = reason

    def mark_failed(self, reason: str, now: datetime):
        self._status = TransactionStatus.failed
        self._rejection_reason = reason
        self._completed_at = now

    def mark_cancelled(self, reason: str, now: datetime):
        self._status = TransactionStatus.cancelled
        self._rejection_reason = reason
        self._completed_at = now

    def _party_label(self, account, external=None):
        if account is not None:
            return account._account_id
        if external:
            return external
        return "-"

    def get_transaction_info(self):
        return {
            "transaction_id": self._transaction_id,
            "type": self._type,
            "amount": self._amount,
            "currency": self._currency,
            "commission": self._commission,
            "converted_amount": self._converted_amount,
            "sender": self._party_label(self._sender),
            "recipient": self._party_label(
                self._recipient, self._external_recipient
            ),
            "status": self._status,
            "rejection_reason": self._rejection_reason,
            "priority": self._priority,
            "attempts": self._attempts,
            "created_at": self._created_at,
            "scheduled_at": self._scheduled_at,
            "processed_at": self._processed_at,
            "completed_at": self._completed_at,
        }

    def __str__(self):
        return (
            f"Transaction("
            f"id={self._transaction_id}, "
            f"type={self._type.value}, "
            f"amount={self._amount}, "
            f"currency={self._currency.value}, "
            f"commission={self._commission}, "
            f"converted={self._converted_amount}, "
            f"sender={self._party_label(self._sender)}, "
            f"recipient={self._party_label(self._recipient, self._external_recipient)}, "
            f"priority={self._priority}, "
            f"status={self._status.value}, "
            f"attempts={self._attempts}, "
            f"reason={self._rejection_reason}"
            f")"
        )
