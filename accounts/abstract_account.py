import uuid
from abc import ABC, abstractmethod

from .enums import AccountStatus


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
