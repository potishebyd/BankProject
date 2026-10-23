import uuid
import enum
from abc import ABC, abstractmethod


class AccountStatus(enum.Enum):
    active = "ACTIVE"
    frozen = "FROZEN"
    closed = "CLOSED"


class Currency(enum.Enum):
    usd = "USD"
    rub = "RUB"
    eur = "EUR"
    kzt = "KZT"
    cny = "CNY"


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class AbstractAccount(ABC):
    def __init__(
        self,
        owner_data: str,
        balance: int | float = 0,
        status: AccountStatus = AccountStatus.active,
        account_id: str | None = None,
    ):
        self._account_id = account_id or uuid.uuid4().hex[:8]
        self._owner_data = owner_data
        self._balance = balance
        self._status = status

    @abstractmethod
    def deposit(self, amount: int | float):
        pass

    @abstractmethod
    def withdraw(self, amount: int | float):
        pass

    @abstractmethod
    def get_account_info(self):
        pass


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


if __name__ == "__main__":
    # Создание активного и замороженного счетов
    active_check = BankAccount(
        "Sigma", 10.2, AccountStatus.active
    )
    frozen_check = BankAccount(
        "Lox", 4.2, AccountStatus.frozen
    )

    # Операции над замороженным счетом
    for operation in (
        lambda: frozen_check.deposit(2.5),
        lambda: frozen_check.withdraw(2.5),
    ):
        try:
            operation()
        except AccountFrozenError as error:
            print("Error:", error)

    # Валидное пополнение и снятие
    active_check.deposit(5.5)
    print(active_check)

    active_check.withdraw(3.4)
    print(active_check)

    # Проверка недостатка средств
    try:
        active_check.withdraw(100)
    except InsufficientFundsError as error:
        print("Error:", error)
