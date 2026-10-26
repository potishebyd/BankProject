import enum


class AccountStatus(enum.Enum):
    active = "ACTIVE"
    frozen = "FROZEN"
    closed = "CLOSED"


class ClientStatus(enum.Enum):
    active = "ACTIVE"
    blocked = "BLOCKED"
    suspicious = "SUSPICIOUS"


class Currency(enum.Enum):
    usd = "USD"
    rub = "RUB"
    eur = "EUR"
    kzt = "KZT"
    cny = "CNY"


class TransactionType(enum.Enum):
    deposit = "DEPOSIT"
    withdraw = "WITHDRAW"
    transfer = "TRANSFER"
    external = "EXTERNAL"


class TransactionStatus(enum.Enum):
    pending = "PENDING"
    deferred = "DEFERRED"
    processing = "PROCESSING"
    retry = "RETRY"
    completed = "COMPLETED"
    failed = "FAILED"
    cancelled = "CANCELLED"


class AuditLevel(enum.Enum):
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


class RiskLevel(enum.Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
