from .bank_account import BankAccount
from .enums import AccountStatus, Currency
from .exceptions import MinBalanceError


class SavingsAccount(BankAccount):
    def __init__(
        self,
        owner_data: str,
        balance: int | float = 0,
        status: AccountStatus = AccountStatus.active,
        account_id: str | None = None,
        currency: Currency = Currency.usd,
        min_balance: int | float = 0,
        monthly_interest_rate: int | float = 0.01,
    ):
        super().__init__(
            owner_data=owner_data,
            balance=balance,
            status=status,
            account_id=account_id,
            currency=currency,
        )

        self._validate_amount(min_balance, "Incorrect minimal balance")
        self._validate_amount(
            monthly_interest_rate, "Incorrect monthly interest rate"
        )

        if balance < min_balance:
            raise MinBalanceError("Initial balance cannot be below minimal balance")

        self._min_balance = min_balance
        self._monthly_interest_rate = monthly_interest_rate

    def deposit(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount

    def apply_monthly_interest(self):
        self.check_status()
        interest = self._balance * self._monthly_interest_rate
        self._balance += interest
        return interest

    def withdraw(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)

        if self._balance - amount < self._min_balance:
            raise MinBalanceError(
                f"Balance cannot fall below min_balance={self._min_balance}"
            )

        self._balance -= amount

    def get_account_info(self):
        info = super().get_account_info()
        info.update(
            {
                "min_balance": self._min_balance,
                "monthly_interest_rate": self._monthly_interest_rate,
            }
        )
        return info

    def __str__(self):
        return (
            f"SavingsAccount("
            f"id=****{self._account_id[-4:]}, "
            f"owner={self._owner_data}, "
            f"status={self._status.value}, "
            f"balance={self._balance}, "
            f"min_balance={self._min_balance}, "
            f"monthly_rate={self._monthly_interest_rate}, "
            f"currency={self._currency.value}"
            f")"
        )
