from accounts import (
    AccountFrozenError,
    AccountStatus,
    BankAccount,
    Currency,
    InsufficientFundsError,
    InvalidAssetTypeError,
    InvalidOperationError,
    InvestmentAccount,
    MinBalanceError,
    OverdraftLimitError,
    PremiumAccount,
    SavingsAccount,
    TransactionLimitError,
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
