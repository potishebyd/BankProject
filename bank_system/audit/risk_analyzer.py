from datetime import datetime, timedelta

from ..accounts.bank_account import BankAccount
from ..core.enums import Currency, RiskLevel, TransactionType
from ..core.exceptions import InvalidOperationError
from ..transactions.transaction import Transaction


class RiskAssessment:
    def __init__(self, level: RiskLevel, reasons: list[str]):
        self.level = level
        self.reasons = list(reasons)

    def __str__(self):
        reasons = ", ".join(self.reasons) if self.reasons else "none"
        return f"RiskAssessment(level={self.level.value}, reasons={reasons})"


class RiskAnalyzer:
    DEFAULT_RATES = {
        Currency.usd: 1.0,
        Currency.eur: 1.08,
        Currency.rub: 0.011,
        Currency.kzt: 0.0021,
        Currency.cny: 0.14,
    }

    def __init__(
        self,
        large_amount_limit: int | float = 1000,
        frequent_limit: int = 3,
        frequent_window_minutes: int = 10,
        night_start_hour: int = 0,
        night_end_hour: int = 5,
        rates: dict | None = None,
    ):
        BankAccount._validate_amount(large_amount_limit, "Incorrect large amount limit")
        if large_amount_limit == 0:
            raise InvalidOperationError("Large amount limit must be positive")

        if isinstance(frequent_limit, bool) or not isinstance(frequent_limit, int):
            raise ValueError("Incorrect frequent limit")
        if frequent_limit < 1:
            raise ValueError("Frequent limit must be positive")

        if (
            isinstance(frequent_window_minutes, bool)
            or not isinstance(frequent_window_minutes, int)
            or frequent_window_minutes < 1
        ):
            raise ValueError("Incorrect frequent window")

        if (
            isinstance(night_start_hour, bool)
            or not isinstance(night_start_hour, int)
            or isinstance(night_end_hour, bool)
            or not isinstance(night_end_hour, int)
        ):
            raise ValueError("Incorrect night hours")

        self._rates = dict(self.DEFAULT_RATES if rates is None else rates)
        self._validate_rates(self._rates)
        self._large_amount_limit = large_amount_limit
        self._frequent_limit = frequent_limit
        self._frequent_window = timedelta(minutes=frequent_window_minutes)
        self._night_start_hour = night_start_hour
        self._night_end_hour = night_end_hour
        self._operations: list[dict] = []
        self._known_destinations: dict[str, set[str]] = {}

    def analyze(self, transaction: Transaction, now: datetime) -> RiskAssessment:
        reasons = []
        account_key = self._account_key(transaction.sender or transaction.recipient)

        if self._is_large(transaction):
            reasons.append("large amount")

        if self._is_frequent(account_key, now):
            reasons.append("frequent operations")

        if self._is_new_destination(transaction):
            reasons.append("transfer to a new account")

        if self._is_night(now):
            reasons.append("night operation")

        return RiskAssessment(self._level(len(reasons)), reasons)

    def observe(self, transaction: Transaction, now: datetime):
        account = transaction.sender or transaction.recipient
        self._operations.append(
            {
                "account_id": self._account_key(account),
                "timestamp": now,
            }
        )

    def confirm(self, transaction: Transaction):
        sender_key = self._account_key(transaction.sender)
        destination = self._destination_key(transaction)
        if sender_key is None or destination is None:
            return

        self._known_destinations.setdefault(sender_key, set()).add(destination)

    def _level(self, signal_count: int) -> RiskLevel:
        if signal_count >= 2:
            return RiskLevel.high
        if signal_count == 1:
            return RiskLevel.medium
        return RiskLevel.low

    def _is_large(self, transaction: Transaction) -> bool:
        return self._amount_in_usd(transaction) >= self._large_amount_limit

    def _is_frequent(self, account_key: str | None, now: datetime) -> bool:
        if account_key is None:
            return False

        recent = [
            item
            for item in self._operations
            if item["account_id"] == account_key and now - item["timestamp"] <= self._frequent_window
        ]
        return len(recent) + 1 >= self._frequent_limit

    def _is_new_destination(self, transaction: Transaction) -> bool:
        destination = self._destination_key(transaction)
        sender_key = self._account_key(transaction.sender)
        if destination is None or sender_key is None:
            return False

        return destination not in self._known_destinations.get(sender_key, set())

    def _is_night(self, now: datetime) -> bool:
        return self._night_start_hour <= now.hour < self._night_end_hour

    def _amount_in_usd(self, transaction: Transaction) -> float:
        if transaction.currency not in self._rates or Currency.usd not in self._rates:
            raise InvalidOperationError("Unknown currency rate")

        return transaction.amount * self._rates[transaction.currency] / self._rates[Currency.usd]

    def _destination_key(self, transaction: Transaction):
        if transaction.type == TransactionType.transfer and transaction.recipient is not None:
            return transaction.recipient._account_id

        if transaction.type == TransactionType.external and transaction.external_recipient:
            return f"external:{transaction.external_recipient}"

        return None

    @staticmethod
    def _account_key(account):
        if account is None:
            return None
        return account._account_id

    def _validate_rates(self, rates: dict):
        if not isinstance(rates, dict) or not rates:
            raise InvalidOperationError("rates must be a non-empty dict")

        for currency, rate in rates.items():
            if not isinstance(currency, Currency):
                raise InvalidOperationError("Incorrect currency rate")

            BankAccount._validate_amount(rate, "Incorrect currency rate")
            if rate == 0:
                raise InvalidOperationError("Currency rate must be positive")
