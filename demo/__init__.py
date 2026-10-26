from .audit import run as run_audit
from .bank_account import run as run_bank_account
from .day6 import run as run_day6
from .day7 import run as run_day7
from .banking import run as run_banking
from .investment_account import run as run_investment_account
from .premium_account import run as run_premium_account
from .savings_account import run as run_savings_account
from .transactions import run as run_transactions


def main():
    run_bank_account()
    run_savings_account()
    run_premium_account()
    run_investment_account()
    run_banking()
    run_transactions()
    run_audit()
    run_day6()
    run_day7()


__all__ = [
    "main",
    "run_audit",
    "run_bank_account",
    "run_day6",
    "run_day7",
    "run_banking",
    "run_investment_account",
    "run_premium_account",
    "run_savings_account",
    "run_transactions",
]
