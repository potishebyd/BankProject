from datetime import datetime

from accounts import (
    AccountFrozenError,
    AccountStatus,
    AuthenticationError,
    Bank,
    BankAccount,
    ClientBlockedError,
    Currency,
    InsufficientFundsError,
    InvalidAssetTypeError,
    InvalidOperationError,
    InvestmentAccount,
    MinBalanceError,
    NightOperationError,
    OverdraftLimitError,
    PremiumAccount,
    SavingsAccount,
    TransactionLimitError,
    UnderageClientError,
)


if __name__ == "__main__":
    # --- BankAccount ---
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
    anna_savings = bank.open_account(
        anna.client_id,
        "anna-secret",
        3000,
        account_class=SavingsAccount,
        min_balance=200,
    )
    ivan_premium = bank.open_account(
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
