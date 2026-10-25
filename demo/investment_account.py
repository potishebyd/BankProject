import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import InvestmentAccount
from bank_system.core import (
    Currency,
    InsufficientFundsError,
    InvalidAssetTypeError,
)


def run():
    print("\n--- InvestmentAccount ---")
    investment_clara = InvestmentAccount("Clara", 5000)
    investment_dmitry = InvestmentAccount(
        "Dmitry", 3000, currency=Currency.usd
    )

    investment_clara.deposit(500)
    investment_clara.invest("stocks", 2000)
    investment_clara.invest("bonds", 1500)
    investment_clara.invest("etf", 500)
    print(investment_clara)

    demo_rates = {"stocks": 0.10, "bonds": 0.04, "etf": 0.07}
    growth = investment_clara.project_yearly_growth(demo_rates)
    print("Clara yearly growth:", growth)
    print(investment_clara.get_account_info())

    investment_dmitry.invest("etf", 1000)
    investment_dmitry.withdraw(500)
    print(investment_dmitry)

    try:
        investment_clara.invest("crypto", 100)
    except InvalidAssetTypeError as error:
        print("Error:", error)

    try:
        investment_clara.invest("stocks", 2000)
    except InsufficientFundsError as error:
        print("Error:", error)

    try:
        investment_dmitry.withdraw(2000)
    except InsufficientFundsError as error:
        print("Error:", error)


if __name__ == "__main__":
    run()
