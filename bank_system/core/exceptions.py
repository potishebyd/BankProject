class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class MinBalanceError(Exception):
    pass


class OverdraftLimitError(Exception):
    pass


class TransactionLimitError(Exception):
    pass


class InvalidAssetTypeError(Exception):
    pass


class UnderageClientError(Exception):
    pass


class ClientNotFoundError(Exception):
    pass


class ClientBlockedError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class NightOperationError(Exception):
    pass


class AccountNotFoundError(Exception):
    pass


class DuplicateClientError(Exception):
    pass


class TransactionNotFoundError(Exception):
    pass
