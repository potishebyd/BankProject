import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.audit import AuditLog, AuditReport, RiskAnalyzer
from bank_system.banking import Bank
from bank_system.core import AuditLevel, Currency, TransactionType
from bank_system.transactions import Transaction, TransactionProcessor, TransactionQueue


class Clock:
    def __init__(self, moment):
        self.moment = moment

    def now(self):
        return self.moment

    def set(self, moment):
        self.moment = moment


def run():
    print("\n--- Audit / Risk ---")
    clock = Clock(datetime(2026, 10, 26, 12, 0))
    log_path = "logs/day5_audit.log"
    audit_log = AuditLog(log_path, now_func=clock.now)
    analyzer = RiskAnalyzer(
        large_amount_limit=1000,
        frequent_limit=3,
        frequent_window_minutes=10,
    )
    bank = Bank(
        "Audit Bank",
        now_func=clock.now,
        audit_log=audit_log,
        risk_analyzer=analyzer,
    )
    anna = bank.add_client("Anna Petrova", 30, password="pass")
    boris = bank.add_client("Boris Orlov", 41, password="pass")
    anna_acc = bank.open_account(anna.client_id, "pass", 20_000)
    boris_acc = bank.open_account(boris.client_id, "pass", 1_000)
    queue = TransactionQueue()
    processor = TransactionProcessor(
        max_attempts=1,
        now_func=clock.now,
        bank=bank,
    )

    def perform(transaction, moment):
        clock.set(moment)
        queue.add(transaction)
        finished = processor.process_queue(queue)
        result = finished[-1]
        print(
            moment.strftime("%d.%m %H:%M"),
            result.type.value,
            result.amount,
            result.status.value,
            result.rejection_reason,
        )
        return result

    perform(
        Transaction(
            TransactionType.transfer,
            100,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 26, 12, 0),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            150,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 26, 12, 1),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            120,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 26, 12, 2),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            2000,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 26, 12, 40),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            80,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 27, 2, 0),
    )
    perform(
        Transaction(
            TransactionType.external,
            90,
            Currency.usd,
            sender=anna_acc,
            external_recipient="EXT-NEW",
        ),
        datetime(2026, 10, 27, 2, 20),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            2500,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 27, 2, 40),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            60,
            Currency.usd,
            sender=boris_acc,
            recipient=anna_acc,
        ),
        datetime(2026, 10, 27, 15, 0),
    )
    perform(
        Transaction(
            TransactionType.withdraw,
            40,
            Currency.usd,
            sender=anna_acc,
        ),
        datetime(2026, 10, 27, 15, 30),
    )
    perform(
        Transaction(
            TransactionType.transfer,
            100_000,
            Currency.usd,
            sender=anna_acc,
            recipient=boris_acc,
        ),
        datetime(2026, 10, 27, 16, 0),
    )

    report = AuditReport(audit_log)
    print("Suspicious:")
    for record in report.suspicious_operations():
        print(record["level"].value, record["actor"], record["message"])

    for actor in ("Anna Petrova", "Boris Orlov"):
        profile = report.client_risk_profile(actor)
        counts = {
            level.value: count for level, count in profile["risk_counts"].items()
        }
        print("Profile:", profile["actor"], profile["level"].value, counts)

    print("Error statistics:", report.error_statistics())
    print("Anna status:", anna.status.value)
    print("Anna balance:", anna_acc._balance)
    print("Boris balance:", boris_acc._balance)

    restored = AuditLog(log_path, restore=True)
    print("Loaded from file:", len(restored.records))
    print(
        "Critical in file:",
        len(restored.filter(level=AuditLevel.critical)),
    )
    print("Night query:", len(restored.filter(query="night")))


if __name__ == "__main__":
    run()
