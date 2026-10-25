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
