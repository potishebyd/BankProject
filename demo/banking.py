import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import (
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from bank_system.banking import Bank
from bank_system.core import (
    AccountFrozenError,
    AuthenticationError,
    ClientBlockedError,
    Currency,
    NightOperationError,
    UnderageClientError,
)


def run():
    print("\n--- Bank / Client ---")
    bank = Bank("Demo Bank", now_func=lambda: datetime(2026, 10, 25, 12, 0))

    anna = bank.add_client(
        "Anna Petrova",
        28,
        password="anna-secret",
        contacts={"phone": "+10000000001", "email": "anna@example.com"},
    )
    ivan = bank.add_client(
        "Ivan Sokolov",
        35,
        password="ivan-secret",
        contacts={"phone": "+10000000002"},
    )
    olga = bank.add_client(
        "Olga Smirnova",
        22,
        password="olga-secret",
        contacts={"email": "olga@example.com"},
    )
    print(anna)
    print(ivan)
    print(olga)

    try:
        bank.add_client("Teen Client", 16, password="too-young")
    except UnderageClientError as error:
        print("Error:", error)

    anna_checking = bank.open_account(anna.client_id, "anna-secret", 1500)
    bank.open_account(
        anna.client_id,
        "anna-secret",
        3000,
        account_class=SavingsAccount,
        min_balance=200,
    )
    bank.open_account(
        ivan.client_id,
        "ivan-secret",
        800,
        currency=Currency.eur,
        account_class=PremiumAccount,
        overdraft_limit=200,
        commission=5,
    )
    olga_invest = bank.open_account(
        olga.client_id,
        "olga-secret",
        5000,
        account_class=InvestmentAccount,
    )
    olga_invest.invest("stocks", 2000)

    print(
        "Anna accounts:",
        [str(item) for item in bank.search_accounts(client_id=anna.client_id)],
    )
    print("Search Petrova:", [str(item) for item in bank.search_accounts("Petrova")])

    print("Authenticated:", bank.authenticate_client(anna.client_id, "anna-secret"))

    try:
        bank.authenticate_client(ivan.client_id, "wrong")
    except AuthenticationError as error:
        print("Error:", error)

    try:
        bank.authenticate_client(ivan.client_id, "wrong")
    except AuthenticationError as error:
        print("Error:", error)

    try:
        bank.authenticate_client(ivan.client_id, "wrong")
    except ClientBlockedError as error:
        print("Error:", error)

    try:
        bank.open_account(ivan.client_id, "ivan-secret", 10)
    except ClientBlockedError as error:
        print("Error:", error)

    bank.freeze_account(anna.client_id, "anna-secret", anna_checking._account_id)
    try:
        anna_checking.withdraw(10)
    except AccountFrozenError as error:
        print("Error:", error)

    bank.unfreeze_account(anna.client_id, "anna-secret", anna_checking._account_id)
    anna_checking.withdraw(10)
    print(anna_checking)

    bank.close_account(olga.client_id, "olga-secret", olga_invest._account_id)
    print(
        "Olga accounts after close:",
        [str(item) for item in bank.search_accounts(client_id=olga.client_id)],
    )

    print("Total balance:", bank.get_total_balance())
    print("Ranking:", bank.get_clients_ranking())
    print("Suspicious actions:", len(bank.suspicious_actions))

    night_bank = Bank(
        "Night Bank",
        now_func=lambda: datetime(2026, 10, 25, 2, 15),
    )
    night_client = night_bank.add_client("Night Owl", 30, password="night-secret")
    try:
        night_bank.open_account(night_client.client_id, "night-secret", 100)
    except NightOperationError as error:
        print("Error:", error)


if __name__ == "__main__":
    run()
