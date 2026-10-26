import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bank_system.audit import AuditLog, RiskAnalyzer
from bank_system.banking import Bank
from bank_system.core import Currency, TransactionType
from bank_system.reports import ReportBuilder
from bank_system.transactions import Transaction, TransactionProcessor, TransactionQueue


class Clock:
    def __init__(self, moment):
        self.moment = moment

    def now(self):
        return self.moment

    def set(self, moment):
        self.moment = moment


def run():
    print("\n=== День 7. Отчёты и графики ===")
    clock = Clock(datetime(2026, 10, 28, 11, 0))
    audit_log = AuditLog("logs/day7_audit.log", now_func=clock.now)
    bank = Bank(
        "Horizon Bank",
        now_func=clock.now,
        audit_log=audit_log,
        risk_analyzer=RiskAnalyzer(),
    )
    queue = TransactionQueue()
    processor = TransactionProcessor(max_attempts=1, now_func=clock.now, bank=bank)

    anna = bank.add_client("Anna Petrova", 31, "pass")
    boris = bank.add_client("Boris Orlov", 44, "pass")
    clara = bank.add_client("Clara Kim", 29, "pass")
    dmitry = bank.add_client("Dmitry Volkov", 38, "pass")
    anna_acc = bank.open_account(anna.client_id, "pass", 4_000)
    boris_acc = bank.open_account(boris.client_id, "pass", 3_000)
    clara_acc = bank.open_account(clara.client_id, "pass", 2_000)
    dmitry_acc = bank.open_account(dmitry.client_id, "pass", 500)

    def transfer(sender, recipient, amount, moment):
        clock.set(moment)
        queue.add(
            Transaction(
                TransactionType.transfer,
                amount,
                Currency.usd,
                sender=sender,
                recipient=recipient,
            )
        )
        processor.process_queue(queue)

    def external(sender, name, amount, moment):
        clock.set(moment)
        queue.add(
            Transaction(
                TransactionType.external,
                amount,
                Currency.usd,
                sender=sender,
                external_recipient=name,
            )
        )
        processor.process_queue(queue)

    transfer(anna_acc, boris_acc, 200, datetime(2026, 10, 28, 11, 0))
    transfer(boris_acc, anna_acc, 80, datetime(2026, 10, 28, 11, 5))
    transfer(anna_acc, boris_acc, 50, datetime(2026, 10, 28, 11, 10))
    clock.set(datetime(2026, 10, 28, 11, 15))
    queue.add(Transaction(TransactionType.deposit, 300, Currency.usd, recipient=anna_acc))
    processor.process_queue(queue)
    transfer(clara_acc, dmitry_acc, 40, datetime(2026, 10, 28, 12, 0))
    transfer(clara_acc, dmitry_acc, 40, datetime(2026, 10, 28, 12, 2))
    transfer(clara_acc, dmitry_acc, 40, datetime(2026, 10, 28, 12, 4))
    transfer(boris_acc, anna_acc, 1_500, datetime(2026, 10, 28, 13, 0))
    transfer(dmitry_acc, boris_acc, 30, datetime(2026, 10, 28, 14, 0))
    transfer(dmitry_acc, boris_acc, 5_000, datetime(2026, 10, 28, 14, 10))
    external(anna_acc, "EXT-900", 100, datetime(2026, 10, 29, 2, 20))

    builder = ReportBuilder(bank, audit_log)
    output = Path("reports/day7")
    client = builder.client_report("Anna Petrova")
    bank_report = builder.bank_report()
    risk = builder.risk_report()

    print(builder.to_text(client))
    print()
    print(builder.to_text(bank_report))
    print()
    print(builder.to_text(risk))

    files = [
        builder.export_to_json(client, str(output / "client_anna.json")),
        builder.export_to_csv(client, str(output / "client_anna.csv")),
        output / "client_anna.txt",
        builder.export_to_json(bank_report, str(output / "bank.json")),
        builder.export_to_csv(bank_report, str(output / "bank.csv")),
        output / "bank.txt",
        builder.export_to_json(risk, str(output / "risk.json")),
        builder.export_to_csv(risk, str(output / "risk.csv")),
        output / "risk.txt",
    ]
    (output / "client_anna.txt").write_text(builder.to_text(client), encoding="utf-8")
    (output / "bank.txt").write_text(builder.to_text(bank_report), encoding="utf-8")
    (output / "risk.txt").write_text(builder.to_text(risk), encoding="utf-8")
    charts = builder.save_charts(str(output / "charts"))

    print("\nФайлы:")
    for path in files:
        print(f"  {path}")
    for name, path in charts.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    run()
