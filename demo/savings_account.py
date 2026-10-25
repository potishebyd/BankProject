import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import SavingsAccount
from bank_system.core import Currency, MinBalanceError


def run():
    print("\n--- SavingsAccount ---")
    savings_anna = SavingsAccount(
        "Anna",
        1000,
        min_balance=200,
        monthly_interest_rate=0.02,
    )
    savings_ivan = SavingsAccount(
        "Ivan",
        500,
        min_balance=100,
        monthly_interest_rate=0.015,
        currency=Currency.rub,
    )

    savings_anna.deposit(100)
    interest = savings_anna.apply_monthly_interest()
    print("Anna interest:", interest)
    print(savings_anna)
    print(savings_anna.get_account_info())

    savings_ivan.withdraw(50)
    print(savings_ivan)

    try:
        savings_ivan.withdraw(400)
    except MinBalanceError as error:
        print("Error:", error)


if __name__ == "__main__":
    run()
