import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import PremiumAccount
from bank_system.core import (
    Currency,
    InvalidOperationError,
    OverdraftLimitError,
    TransactionLimitError,
)


def run():
    print("\n--- PremiumAccount ---")
    premium_boris = PremiumAccount(
        "Boris",
        500,
        overdraft_limit=300,
        commission=5,
        max_transaction_amount=10_000,
    )
    premium_olga = PremiumAccount(
        "Olga",
        2000,
        overdraft_limit=1500,
        commission=15,
        max_transaction_amount=50_000,
        currency=Currency.eur,
    )

    premium_boris.withdraw(700)
    print(premium_boris)
    print(premium_boris.get_account_info())

    premium_olga.deposit(200)
    premium_olga.withdraw(100)
    print(premium_olga)

    try:
        premium_boris.withdraw(200)
    except OverdraftLimitError as error:
        print("Error:", error)

    try:
        premium_olga.withdraw(60_000)
    except TransactionLimitError as error:
        print("Error:", error)

    try:
        premium_olga.deposit(60_000)
    except TransactionLimitError as error:
        print("Error:", error)

    try:
        premium_olga.deposit(10)
    except InvalidOperationError as error:
        print("Error:", error)


if __name__ == "__main__":
    run()
