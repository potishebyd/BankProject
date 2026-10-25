import math

from .abstract_account import AbstractAccount
from .enums import AccountStatus, Currency
from .exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)


class BankAccount(AbstractAccount):
    def __init__(
        self,
        owner_data: str,
        balance: int | float = 0,
        status: AccountStatus = AccountStatus.active,
        account_id: str | None = None,
        currency: Currency = Currency.usd,
    ):
        if not isinstance(owner_data, str) or not owner_data.strip():
            raise ValueError("Incorrect owner name")

        self._validate_amount(balance, "Incorrect initial balance")

        if balance < 0:
            raise ValueError("Initial balance cannot be negative")

        if not isinstance(status, AccountStatus):
            raise ValueError("Incorrect status")

        if account_id is not None:
            if not isinstance(account_id, str) or not account_id:
                raise ValueError("Incorrect account id")

        if not isinstance(currency, Currency):
            raise ValueError("Incorrect currency")

        super().__init__(
            owner_data=owner_data,
            balance=balance,
            status=status,
            account_id=account_id,
        )

        self._currency = currency

    @staticmethod
    def _validate_amount(amount, message="Incorrect amount"):
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise InvalidOperationError(message)

        if not math.isfinite(amount):
            raise InvalidOperationError(message)

        if amount < 0:
            raise InvalidOperationError("Amount cannot be negative")

    def check_status(self):
        if self._status == AccountStatus.frozen:
            raise AccountFrozenError("Account is frozen")

        if self._status == AccountStatus.closed:
            raise AccountClosedError("Account is closed")

    def check_amount(self, amount):
        self._validate_amount(amount)

    def deposit(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount

    def withdraw(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Insufficient balance")

        self._balance -= amount

    def get_account_info(self):
        return {
            "account_id": self._account_id,
            "owner_data": self._owner_data,
            "balance": self._balance,
            "status": self._status,
            "currency": self._currency,
        }

    def __str__(self):
        return (
            f"BankAccount("
            f"id=****{self._account_id[-4:]}, "
            f"owner={self._owner_data}, "
            f"status={self._status.value}, "
            f"balance={self._balance}, "
            f"currency={self._currency.value}"
            f")"
        )
