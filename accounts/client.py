import uuid

from .enums import ClientStatus
from .exceptions import UnderageClientError


class Client:
    MIN_AGE = 18
    MAX_FAILED_ATTEMPTS = 3

    def __init__(
        self,
        full_name: str,
        age: int,
        password: str,
        contacts: dict | None = None,
        client_id: str | None = None,
        status: ClientStatus = ClientStatus.active,
    ):
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValueError("Incorrect full name")

        if isinstance(age, bool) or not isinstance(age, int):
            raise ValueError("Incorrect age")

        if age < self.MIN_AGE:
            raise UnderageClientError("Client must be at least 18 years old")

        if not isinstance(password, str) or not password:
            raise ValueError("Incorrect password")

        if contacts is None:
            contacts = {}
        elif not isinstance(contacts, dict):
            raise ValueError("Incorrect contacts")

        if client_id is not None:
            if not isinstance(client_id, str) or not client_id:
                raise ValueError("Incorrect client id")

        if not isinstance(status, ClientStatus):
            raise ValueError("Incorrect status")

        self._full_name = full_name.strip()
        self._age = age
        self._password = password
        self._contacts = dict(contacts)
        self._client_id = client_id or uuid.uuid4().hex[:8]
        self._status = status
        self._account_numbers: list[str] = []
        self._failed_login_attempts = 0

    @property
    def client_id(self):
        return self._client_id

    @property
    def full_name(self):
        return self._full_name

    @property
    def age(self):
        return self._age

    @property
    def status(self):
        return self._status

    @property
    def contacts(self):
        return dict(self._contacts)

    @property
    def account_numbers(self):
        return list(self._account_numbers)

    @property
    def failed_login_attempts(self):
        return self._failed_login_attempts

    def add_account_number(self, account_id: str):
        if account_id not in self._account_numbers:
            self._account_numbers.append(account_id)

    def remove_account_number(self, account_id: str):
        if account_id in self._account_numbers:
            self._account_numbers.remove(account_id)

    def check_password(self, password: str) -> bool:
        return password == self._password

    def register_failed_login(self):
        self._failed_login_attempts += 1
        if self._failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            self._status = ClientStatus.blocked

    def reset_failed_logins(self):
        self._failed_login_attempts = 0

    def mark_suspicious(self):
        if self._status != ClientStatus.blocked:
            self._status = ClientStatus.suspicious

    def block(self):
        self._status = ClientStatus.blocked

    def is_blocked(self) -> bool:
        return self._status == ClientStatus.blocked

    def get_client_info(self):
        return {
            "client_id": self._client_id,
            "full_name": self._full_name,
            "age": self._age,
            "status": self._status,
            "contacts": self.contacts,
            "account_numbers": self.account_numbers,
        }

    def __str__(self):
        return (
            f"Client("
            f"id={self._client_id}, "
            f"name={self._full_name}, "
            f"age={self._age}, "
            f"status={self._status.value}, "
            f"accounts={len(self._account_numbers)}"
            f")"
        )
