import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.accounts import PremiumAccount
from bank_system.banking import Bank
from bank_system.core import Currency, TransactionType
from bank_system.transactions import (
    Transaction,
    TransactionProcessor,
    TransactionQueue,
)


def run():
    print("\n--- Transactions ---")
    moment = datetime(2026, 10, 25, 12, 0)
    tx_bank = Bank("Tx Bank", now_func=lambda: moment)
    anna_tx = tx_bank.add_client("Anna Petrova", 30, password="pass")
    boris_tx = tx_bank.add_client("Boris Orlov", 41, password="pass")
    clara_tx = tx_bank.add_client("Clara Kim", 27, password="pass")
    kira_tx = tx_bank.add_client("Kira Volkov", 24, password="pass")

    anna_acc = tx_bank.open_account(anna_tx.client_id, "pass", 1000)
    boris_acc = tx_bank.open_account(boris_tx.client_id, "pass", 400)
    clara_acc = tx_bank.open_account(
        clara_tx.client_id,
        "pass",
        0,
        currency=Currency.eur,
        account_class=PremiumAccount,
        overdraft_limit=500,
        commission=0,
    )
    clara_acc._balance = -20
    frozen_acc = tx_bank.open_account(anna_tx.client_id, "pass", 250)
    tx_bank.freeze_account(anna_tx.client_id, "pass", frozen_acc._account_id)
    negative_acc = tx_bank.open_account(kira_tx.client_id, "pass", 0)
    negative_acc._balance = -15

    queue = TransactionQueue()
    transactions = [
        (
            Transaction(
                TransactionType.transfer,
                50,
                Currency.usd,
                sender=boris_acc,
                recipient=anna_acc,
            ),
            5,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                100,
                Currency.usd,
                sender=anna_acc,
                recipient=boris_acc,
            ),
            1,
            None,
        ),
        (
            Transaction(
                TransactionType.external,
                200,
                Currency.usd,
                sender=anna_acc,
                external_recipient="EXT-1001",
            ),
            2,
            None,
        ),
        (
            Transaction(
                TransactionType.deposit,
                300,
                Currency.usd,
                recipient=anna_acc,
            ),
            0,
            None,
        ),
        (
            Transaction(
                TransactionType.withdraw,
                40,
                Currency.usd,
                sender=boris_acc,
            ),
            0,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                100,
                Currency.usd,
                sender=anna_acc,
                recipient=clara_acc,
            ),
            3,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                20,
                Currency.usd,
                sender=frozen_acc,
                recipient=boris_acc,
            ),
            0,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                10,
                Currency.usd,
                sender=negative_acc,
                recipient=anna_acc,
            ),
            0,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                30,
                Currency.eur,
                sender=clara_acc,
                recipient=anna_acc,
            ),
            4,
            None,
        ),
        (
            Transaction(
                TransactionType.transfer,
                10,
                Currency.usd,
                sender=anna_acc,
                recipient=boris_acc,
            ),
            0,
            datetime(2026, 10, 25, 18, 0),
        ),
    ]

    for transaction, priority, scheduled_at in transactions:
        queue.add(transaction, priority=priority, scheduled_at=scheduled_at)

    print("Queued:", len(queue))
    processor = TransactionProcessor(
        rates={
            Currency.usd: 1.0,
            Currency.eur: 1.25,
            Currency.rub: 0.01,
            Currency.kzt: 0.002,
            Currency.cny: 0.14,
        },
        external_commission_rate=0.02,
        max_attempts=2,
        now_func=lambda: moment,
    )
    finished = processor.process_queue(queue)

    print("Finished:")
    for transaction in finished:
        print(transaction)

    print("Still queued:", [str(item) for item in queue.transactions])
    cancelled = queue.cancel(transactions[-1][0].transaction_id, now=moment)
    print("Cancelled:", cancelled)
    print("Queue after cancel:", len(queue))
    print("Errors:")
    for error in processor.errors:
        print(error)

    print("Anna:", anna_acc)
    print("Boris:", boris_acc)
    print("Clara:", clara_acc)
    print("Frozen:", frozen_acc)
    print("Negative:", negative_acc)


if __name__ == "__main__":
    run()
