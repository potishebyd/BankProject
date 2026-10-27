from datetime import datetime

from ..accounts.bank_account import BankAccount
from ..audit.risk_analyzer import RiskAnalyzer
from ..core.enums import AccountStatus, AuditLevel, Currency, RiskLevel
from ..core.exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    ClientBlockedError,
    ClientNotFoundError,
    DuplicateClientError,
    HighRiskError,
    InvalidOperationError,
    NightOperationError,
)
from .client import Client


class Bank:
    NIGHT_START_HOUR = 0
    NIGHT_END_HOUR = 5

    def __init__(
        self,
        name: str = "Bank",
        now_func=datetime.now,
        audit_log=None,
        risk_analyzer: RiskAnalyzer | None = None,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Incorrect bank name")

        if risk_analyzer is not None and not isinstance(risk_analyzer, RiskAnalyzer):
            raise ValueError("Incorrect risk analyzer")

        self._name = name.strip()
        self._now = now_func
        self._clients: dict[str, Client] = {}
        self._accounts: dict[str, BankAccount] = {}
        self._suspicious_actions: list[dict] = []
        self._audit_log = audit_log
        self._risk_analyzer = risk_analyzer

    @property
    def name(self):
        return self._name

    @property
    def suspicious_actions(self):
        return list(self._suspicious_actions)

    def _mark_suspicious(self, description: str, client_id: str | None = None):
        record = {
            "timestamp": self._now(),
            "description": description,
            "client_id": client_id,
        }
        self._suspicious_actions.append(record)

        if client_id and client_id in self._clients:
            self._clients[client_id].mark_suspicious()

    def _ensure_business_hours(self, operation: str, client_id: str | None = None):
        hour = self._now().hour
        if self.NIGHT_START_HOUR <= hour < self.NIGHT_END_HOUR:
            self._mark_suspicious(
                f"Night operation attempt: {operation}",
                client_id=client_id,
            )
            raise NightOperationError(
                "Operations are forbidden from 00:00 to 05:00"
            )

    def _get_client(self, client_id: str) -> Client:
        client = self._clients.get(client_id)
        if client is None:
            raise ClientNotFoundError("Client not found")
        return client

    def _get_account(self, account_id: str) -> BankAccount:
        account = self._accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError("Account not found")
        return account

    def authenticate_client(self, client_id: str, password: str) -> bool:
        client = self._get_client(client_id)

        if client.is_blocked():
            self._mark_suspicious("Login attempt while blocked", client_id)
            raise ClientBlockedError("Client is blocked")

        if client.check_password(password):
            client.reset_failed_logins()
            return True

        client.register_failed_login()
        self._mark_suspicious("Failed login attempt", client_id)

        if client.is_blocked():
            raise ClientBlockedError(
                "Client is blocked after 3 failed login attempts"
            )

        raise AuthenticationError("Invalid credentials")

    def add_client(
        self,
        full_name: str,
        age: int,
        password: str,
        contacts: dict | None = None,
        client_id: str | None = None,
    ) -> Client:
        if client_id is not None and client_id in self._clients:
            raise DuplicateClientError("Client with this id already exists")

        client = Client(
            full_name=full_name,
            age=age,
            password=password,
            contacts=contacts,
            client_id=client_id,
        )

        if client.client_id in self._clients:
            raise DuplicateClientError("Client with this id already exists")

        self._clients[client.client_id] = client
        return client

    def open_account(
        self,
        client_id: str,
        password: str,
        initial_balance: int | float = 0,
        currency: Currency = Currency.usd,
        account_class=BankAccount,
        **account_kwargs,
    ) -> BankAccount:
        self._ensure_business_hours("open_account", client_id)
        self.authenticate_client(client_id, password)

        client = self._get_client(client_id)
        account = account_class(
            owner_data=client.full_name,
            balance=initial_balance,
            currency=currency,
            **account_kwargs,
        )
        account.bind_clock(self._now)
        self._accounts[account._account_id] = account
        client.add_account_number(account._account_id)
        return account

    def close_account(self, client_id: str, password: str, account_id: str):
        self._ensure_business_hours("close_account", client_id)
        self.authenticate_client(client_id, password)
        self._ensure_client_owns_account(client_id, account_id)

        account = self._get_account(account_id)
        if account._status == AccountStatus.closed:
            raise InvalidOperationError("Account is already closed")

        account._status = AccountStatus.closed

    def freeze_account(self, client_id: str, password: str, account_id: str):
        self._ensure_business_hours("freeze_account", client_id)
        self.authenticate_client(client_id, password)
        self._ensure_client_owns_account(client_id, account_id)

        account = self._get_account(account_id)
        if account._status == AccountStatus.closed:
            raise InvalidOperationError("Cannot freeze a closed account")

        if account._status == AccountStatus.frozen:
            raise InvalidOperationError("Account is already frozen")

        account._status = AccountStatus.frozen

    def unfreeze_account(self, client_id: str, password: str, account_id: str):
        self._ensure_business_hours("unfreeze_account", client_id)
        self.authenticate_client(client_id, password)
        self._ensure_client_owns_account(client_id, account_id)

        account = self._get_account(account_id)
        if account._status != AccountStatus.frozen:
            raise InvalidOperationError("Account is not frozen")

        account._status = AccountStatus.active

    def _ensure_client_owns_account(self, client_id: str, account_id: str):
        client = self._get_client(client_id)
        if account_id not in client.account_numbers:
            self._mark_suspicious(
                f"Access to foreign account {account_id}",
                client_id,
            )
            raise InvalidOperationError("Account does not belong to this client")

    def search_accounts(
        self,
        query: str | None = None,
        client_id: str | None = None,
        status: AccountStatus | None = None,
    ) -> list[BankAccount]:
        accounts = list(self._accounts.values())

        if client_id is not None:
            client = self._get_client(client_id)
            owned = set(client.account_numbers)
            accounts = [
                account
                for account in accounts
                if account._account_id in owned
            ]

        if status is not None:
            accounts = [
                account for account in accounts if account._status == status
            ]

        if query:
            needle = query.lower()
            accounts = [
                account
                for account in accounts
                if needle in account._owner_data.lower()
                or needle in account._account_id.lower()
                or needle in account._status.value.lower()
            ]

        return accounts

    def _account_value(self, account: BankAccount) -> int | float:
        info = account.get_account_info()
        return info.get("total_value", info["balance"])

    def get_total_balance(self, currency: Currency | None = None) -> dict:
        totals: dict[Currency, int | float] = {}

        for account in self._accounts.values():
            if account._status == AccountStatus.closed:
                continue

            if currency is not None and account._currency != currency:
                continue

            totals[account._currency] = (
                totals.get(account._currency, 0) + self._account_value(account)
            )

        return totals

    def get_clients_ranking(self) -> list[dict]:
        ranking = []

        for client in self._clients.values():
            total = 0
            for account_id in client.account_numbers:
                account = self._accounts[account_id]
                if account._status == AccountStatus.closed:
                    continue
                total += self._account_value(account)

            ranking.append(
                {
                    "client_id": client.client_id,
                    "full_name": client.full_name,
                    "status": client.status,
                    "total_balance": total,
                }
            )

        ranking.sort(key=lambda item: item["total_balance"], reverse=True)
        return ranking

    def review_transaction(self, transaction):
        actor, account_id = self._transaction_actor(transaction)
        client_id = self._client_id_for_account(account_id)
        if self._risk_analyzer is None:
            self._ensure_business_hours("transaction", client_id)
            return None

        now = self._now()
        assessment = self._risk_analyzer.analyze(transaction, now)
        self._risk_analyzer.observe(transaction, now)

        if assessment.level == RiskLevel.high:
            audit_level = AuditLevel.critical
            message = "Dangerous operation blocked: " + ", ".join(assessment.reasons)
        elif assessment.level == RiskLevel.medium:
            audit_level = AuditLevel.warning
            message = "Suspicious operation: " + ", ".join(assessment.reasons)
        else:
            audit_level = AuditLevel.info
            message = "Operation accepted"

        self._write_audit(
            audit_level,
            message,
            transaction,
            actor,
            account_id,
            risk=assessment.level,
            reasons=assessment.reasons,
        )

        if assessment.level == RiskLevel.high:
            self._mark_suspicious(message, client_id)
            raise HighRiskError(message)

        self._ensure_business_hours("transaction", client_id)
        return assessment

    def confirm_transaction(self, transaction):
        if self._risk_analyzer is not None:
            self._risk_analyzer.confirm(transaction)

    def record_failure(self, transaction, error):
        if isinstance(error, HighRiskError):
            return

        actor, account_id = self._transaction_actor(transaction)
        self._write_audit(
            AuditLevel.error,
            str(error),
            transaction,
            actor,
            account_id,
        )

    def _write_audit(
        self,
        level,
        message,
        transaction,
        actor,
        account_id,
        risk=None,
        reasons=None,
    ):
        if self._audit_log is None:
            return

        self._audit_log.record(
            level,
            message,
            actor=actor,
            account_id=account_id,
            transaction_id=transaction.transaction_id,
            transaction_type=transaction.type.value,
            amount=transaction.amount,
            currency=transaction.currency.value,
            risk=risk,
            reasons=reasons,
        )

    @staticmethod
    def _transaction_actor(transaction):
        account = transaction.sender or transaction.recipient
        if account is None:
            return None, None
        return account._owner_data, account._account_id

    def _client_id_for_account(self, account_id: str | None):
        if account_id is None:
            return None

        for client in self._clients.values():
            if account_id in client.account_numbers:
                return client.client_id

        return None
