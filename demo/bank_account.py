import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import BankAccount
from bank_system.core import (
    AccountFrozenError,
    AccountStatus,
    InsufficientFundsError,
)


def run():
    active_check = BankAccount("Sigma", 10.2, AccountStatus.active)
    frozen_check = BankAccount("Lox", 4.2, AccountStatus.frozen)

    for operation in (
        lambda: frozen_check.deposit(2.5),
        lambda: frozen_check.withdraw(2.5),
    ):
        try:
            operation()
        except AccountFrozenError as error:
            print("Error:", error)

    active_check.deposit(5.5)
    print(active_check)
    active_check.withdraw(3.4)
    print(active_check)

    try:
        active_check.withdraw(100)
    except InsufficientFundsError as error:
        print("Error:", error)


if __name__ == "__main__":
    run()
