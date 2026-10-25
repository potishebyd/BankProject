from ..core.enums import AccountStatus, Currency
from ..core.exceptions import (
    InsufficientFundsError,
    InvalidAssetTypeError,
    InvalidOperationError,
)
from .bank_account import BankAccount


class InvestmentAccount(BankAccount):
    ALLOWED_ASSETS = ("stocks", "bonds", "etf")

    def __init__(
        self,
        owner_data: str,
        balance: int | float = 0,
        status: AccountStatus = AccountStatus.active,
        account_id: str | None = None,
        currency: Currency = Currency.usd,
    ):
        super().__init__(
            owner_data=owner_data,
            balance=balance,
            status=status,
            account_id=account_id,
            currency=currency,
        )
        self._portfolio = {asset: 0.0 for asset in self.ALLOWED_ASSETS}

    def _check_asset_type(self, asset_type: str):
        if asset_type not in self.ALLOWED_ASSETS:
            raise InvalidAssetTypeError("Invalid asset type")

    def deposit(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount

    def invest(self, asset_type: str, amount: int | float):
        self.check_status()
        self._check_asset_type(asset_type)
        self.check_amount(amount)

        if amount == 0:
            raise InvalidOperationError("Investment amount must be positive")

        if amount > self._balance:
            raise InsufficientFundsError("Insufficient cash for investment")

        self._balance -= amount
        self._portfolio[asset_type] += amount

    def project_yearly_growth(self, growth_rates: dict):
        if not isinstance(growth_rates, dict) or not growth_rates:
            raise InvalidOperationError("growth_rates must be a non-empty dict")

        projected_growth = 0.0

        for asset_type, rate in growth_rates.items():
            self._check_asset_type(asset_type)
            self._validate_amount(rate, "Incorrect growth rate")
            projected_growth += self._portfolio[asset_type] * rate

        return projected_growth

    def withdraw(self, amount: int | float):
        self.check_status()
        self.check_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError(
                "Insufficient cash balance; invested funds are locked"
            )

        self._balance -= amount

    def get_account_info(self):
        invested = sum(self._portfolio.values())
        info = super().get_account_info()
        info.update(
            {
                "cash_balance": self._balance,
                "portfolio": dict(self._portfolio),
                "invested": invested,
                "total_value": self._balance + invested,
            }
        )
        return info

    def __str__(self):
        invested = sum(self._portfolio.values())
        return (
            f"InvestmentAccount("
            f"id=****{self._account_id[-4:]}, "
            f"owner={self._owner_data}, "
            f"status={self._status.value}, "
            f"cash={self._balance}, "
            f"invested={invested}, "
            f"portfolio={self._portfolio}, "
            f"currency={self._currency.value}"
            f")"
        )
