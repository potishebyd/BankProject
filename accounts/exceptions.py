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
