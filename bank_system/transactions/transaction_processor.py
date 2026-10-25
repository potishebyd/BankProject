from datetime import datetime

from ..accounts.bank_account import BankAccount
from ..accounts.premium_account import PremiumAccount
from ..core.enums import Currency, TransactionType
from ..core.exceptions import InvalidOperationError
from .transaction import Transaction
from .transaction_queue import TransactionQueue


class TransactionProcessor:
    DEFAULT_RATES = {
        Currency.usd: 1.0,
        Currency.eur: 1.08,
        Currency.rub: 0.011,
        Currency.kzt: 0.0021,
        Currency.cny: 0.14,
    }

    def __init__(
        self,
        rates: dict | None = None,
        external_commission_rate: int | float = 0.02,
        max_attempts: int = 3,
        now_func=datetime.now,
    ):
        self._rates = dict(self.DEFAULT_RATES if rates is None else rates)
        self._validate_rates(self._rates)
        BankAccount._validate_amount(
            external_commission_rate, "Incorrect external commission rate"
        )

        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise ValueError("Incorrect max attempts")

        if max_attempts < 1:
            raise ValueError("max attempts must be positive")

        self._external_commission_rate = external_commission_rate
        self._max_attempts = max_attempts
        self._now = now_func
        self._errors: list[dict] = []

    @property
    def errors(self):
        return list(self._errors)

    @property
    def external_commission_rate(self):
        return self._external_commission_rate

    def _validate_rates(self, rates: dict):
        if not isinstance(rates, dict) or not rates:
            raise InvalidOperationError("rates must be a non-empty dict")

        for currency, rate in rates.items():
            if not isinstance(currency, Currency):
                raise InvalidOperationError("Incorrect currency rate")

            BankAccount._validate_amount(rate, "Incorrect currency rate")
            if rate == 0:
                raise InvalidOperationError("Currency rate must be positive")

    def convert(
        self,
        amount: int | float,
        from_currency: Currency,
        to_currency: Currency,
    ) -> float:
        if from_currency == to_currency:
            return float(amount)

        if from_currency not in self._rates or to_currency not in self._rates:
            raise InvalidOperationError("Unknown currency rate")

        return amount * self._rates[from_currency] / self._rates[to_currency]

    def _record_error(self, transaction: Transaction, error: Exception):
        self._errors.append(
            {
                "transaction_id": transaction.transaction_id,
                "attempt": transaction.attempts,
                "error": str(error),
                "timestamp": self._now(),
            }
        )

    def _ensure_transfer_allowed(self, account: BankAccount):
        account.check_status()
        if account._balance < 0 and not isinstance(account, PremiumAccount):
            raise InvalidOperationError(
                "Transfers are forbidden when balance is negative"
            )

    def _debit(self, account: BankAccount, amount: int | float, currency: Currency):
        charged = self.convert(amount, currency, account._currency)
        account.withdraw(charged)
        return charged

    def _credit(self, account: BankAccount, amount: int | float, currency: Currency):
        credited = self.convert(amount, currency, account._currency)
        account.deposit(credited)
        return credited

    def _move(self, sender: BankAccount, recipient: BankAccount, amount, currency):
        self._ensure_transfer_allowed(sender)
        recipient.check_status()
        charged = self._debit(sender, amount, currency)
        try:
            credited = self._credit(recipient, amount, currency)
        except Exception:
            BankAccount.deposit(sender, charged)
            raise
        return credited

    def _execute(self, transaction: Transaction):
        if transaction.type == TransactionType.deposit:
            credited = self._credit(
                transaction.recipient, transaction.amount, transaction.currency
            )
            return 0, credited

        if transaction.type == TransactionType.withdraw:
            self._debit(
                transaction.sender, transaction.amount, transaction.currency
            )
            return 0, None

        if transaction.type == TransactionType.transfer:
            credited = self._move(
                transaction.sender,
                transaction.recipient,
                transaction.amount,
                transaction.currency,
            )
            return 0, credited

        if transaction.type == TransactionType.external:
            commission = transaction.amount * self._external_commission_rate
            self._ensure_transfer_allowed(transaction.sender)
            self._debit(
                transaction.sender,
                transaction.amount + commission,
                transaction.currency,
            )
            return commission, None

        raise InvalidOperationError("Unknown transaction type")

    def _run(self, transaction: Transaction):
        transaction.mark_processing(self._now())
        try:
            commission, converted_amount = self._execute(transaction)
        except Exception as error:
            self._record_error(transaction, error)
            raise

        transaction.mark_completed(self._now(), commission, converted_amount)

    def process(self, transaction: Transaction) -> Transaction:
        self._run(transaction)
        return transaction

    def process_queue(self, queue: TransactionQueue) -> list[Transaction]:
        finished = []

        while True:
            transaction = queue.pop_ready(self._now())
            if transaction is None:
                break

            try:
                self._run(transaction)
            except Exception as error:
                if transaction.attempts < self._max_attempts:
                    transaction.mark_retry(str(error))
                    queue.add(transaction)
                else:
                    transaction.mark_failed(str(error), self._now())
                    finished.append(transaction)
            else:
                finished.append(transaction)

        return finished
