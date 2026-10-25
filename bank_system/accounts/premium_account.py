from ..core.enums import AccountStatus, Currency
from ..core.exceptions import (
    InvalidOperationError,
    OverdraftLimitError,
    TransactionLimitError,
)
from .bank_account import BankAccount


class PremiumAccount(BankAccount):
    def __init__(
        self,
        owner_data: str,
        balance: int | float = 0,
        status: AccountStatus = AccountStatus.active,
        account_id: str | None = None,
        currency: Currency = Currency.usd,
        overdraft_limit: int | float = 1000,
        commission: int | float = 10,
        max_transaction_amount: int | float = 100000,
    ):
        super().__init__(
            owner_data=owner_data,
            balance=balance,
            status=status,
            account_id=account_id,
            currency=currency,
        )

        self._validate_amount(overdraft_limit, "Incorrect overdraft_limit")
        self._validate_amount(commission, "Incorrect commission")
        self._validate_amount(
            max_transaction_amount, "Incorrect maximun transaction amount"
        )

        if max_transaction_amount == 0:
            raise InvalidOperationError("Maximun transaction amount must be positive")

        self._overdraft_limit = overdraft_limit
        self._commission = commission
        self._max_transaction_amount = max_transaction_amount

    def _check_transaction_limit(self, amount: int | float):
        if amount > self._max_transaction_amount:
            raise TransactionLimitError("Amount exceeds maximun transaction amount")

    def deposit(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)
        self._check_transaction_limit(amount)

        if amount <= self._commission:
            raise InvalidOperationError("Deposit must be greater than commission")

        self._balance += amount - self._commission

    def withdraw(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)
        self._check_transaction_limit(amount)

        total = amount + self._commission
        if self._balance - total < -self._overdraft_limit:
            raise OverdraftLimitError("Operation exceeds overdraft limit")

        self._balance -= total

    def get_account_info(self):
        info = super().get_account_info()
        info.update(
            {
                "overdraft_limit": self._overdraft_limit,
                "commission": self._commission,
                "max_transaction_amount": self._max_transaction_amount,
                "available_overdraft": self._overdraft_limit
                + min(self._balance, 0),
            }
        )
        return info

    def __str__(self):
        return (
            f"PremiumAccount("
            f"id=****{self._account_id[-4:]}, "
            f"owner={self._owner_data}, "
            f"status={self._status.value}, "
            f"balance={self._balance}, "
            f"overdraft_limit={self._overdraft_limit}, "
            f"commission={self._commission}, "
            f"max_tx={self._max_transaction_amount}, "
            f"currency={self._currency.value}"
            f")"
        )
