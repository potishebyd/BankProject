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
from bank_system.audit import AuditLog, AuditReport, RiskAnalyzer
from bank_system.banking import Bank
from bank_system.core import Currency, TransactionStatus, TransactionType
from bank_system.transactions import Transaction, TransactionProcessor, TransactionQueue


class Clock:
    def __init__(self, moment):
        self.moment = moment

    def now(self):
        return self.moment

    def set(self, moment):
        self.moment = moment


def _label(account, external=None):
    if account is None:
        return external or "-"
    short_type = type(account).__name__.replace("Account", "")
    return f"{account._owner_data}:{short_type}:{account._account_id[-4:]}"


def _describe(transaction):
    return (
        f"{transaction.transaction_id} {transaction.type.value:<8} "
        f"{transaction.amount:>8} {transaction.currency.value} "
        f"{_label(transaction.sender):<32} -> "
        f"{_label(transaction.recipient, transaction.external_recipient):<32} "
        f"p={transaction.priority}"
    )


def run():
    print("\n=== День 6. Демонстрация банка ===")
    clock = Clock(datetime(2026, 10, 26, 10, 0))
    audit_log = AuditLog("logs/day6_audit.log", now_func=clock.now)
    analyzer = RiskAnalyzer()
    bank = Bank(
        "Horizon Bank",
        now_func=clock.now,
        audit_log=audit_log,
        risk_analyzer=analyzer,
    )
    queue = TransactionQueue()
    processor = TransactionProcessor(max_attempts=1, now_func=clock.now, bank=bank)
    results = []

    anna = bank.add_client(
        "Anna Petrova", 31, "pass", {"phone": "+10001", "email": "anna@bank.test"}
    )
    boris = bank.add_client("Boris Orlov", 44, "pass", {"phone": "+10002"})
    clara = bank.add_client("Clara Kim", 29, "pass", {"email": "clara@bank.test"})
    dmitry = bank.add_client("Dmitry Volkov", 38, "pass", {"phone": "+10004"})
    elena = bank.add_client("Elena Sokolova", 27, "pass", {"phone": "+10005"})
    ivan = bank.add_client("Ivan Petrov", 35, "pass", {"phone": "+10006"})
    olga = bank.add_client("Olga Smirnova", 41, "pass", {"email": "olga@bank.test"})

    anna_checking = bank.open_account(anna.client_id, "pass", 6_000)
    anna_savings = bank.open_account(
        anna.client_id, "pass", 8_000, account_class=SavingsAccount, min_balance=500
    )
    boris_checking = bank.open_account(boris.client_id, "pass", 4_000)
    boris_premium = bank.open_account(
        boris.client_id,
        "pass",
        2_500,
        account_class=PremiumAccount,
        overdraft_limit=400,
        commission=0,
    )
    clara_checking = bank.open_account(clara.client_id, "pass", 3_500)
    clara_investment = bank.open_account(
        clara.client_id, "pass", 5_000, account_class=InvestmentAccount
    )
    dmitry_checking = bank.open_account(dmitry.client_id, "pass", 2_000)
    elena_checking = bank.open_account(elena.client_id, "pass", 3_000)
    elena_savings = bank.open_account(
        elena.client_id, "pass", 4_500, account_class=SavingsAccount, min_balance=300
    )
    ivan_checking = bank.open_account(ivan.client_id, "pass", 2_200)
    ivan_premium = bank.open_account(
        ivan.client_id,
        "pass",
        3_000,
        account_class=PremiumAccount,
        overdraft_limit=500,
        commission=0,
    )
    olga_checking = bank.open_account(olga.client_id, "pass", 1_500)
    olga_extra = bank.open_account(olga.client_id, "pass", 200)

    accounts = [
        anna_checking,
        anna_savings,
        boris_checking,
        boris_premium,
        clara_checking,
        clara_investment,
        dmitry_checking,
        elena_checking,
        elena_savings,
        ivan_checking,
        ivan_premium,
        olga_checking,
        olga_extra,
    ]
    print(f"Банк: {bank.name}")
    print(f"Клиентов: {len(bank._clients)}, счетов: {len(accounts)}")

    def transfer(sender, recipient, amount):
        return Transaction(
            TransactionType.transfer,
            amount,
            Currency.usd,
            sender=sender,
            recipient=recipient,
        )

    def enqueue(transaction, priority=0, scheduled_at=None):
        queue.add(transaction, priority=priority, scheduled_at=scheduled_at)
        extra = ""
        if transaction.scheduled_at is not None:
            extra = f" | отложена до {transaction.scheduled_at:%d.%m %H:%M}"
        print(f"  В ОЧЕРЕДИ  {_describe(transaction)}{extra}")
        return transaction

    def process_ready(moment):
        clock.set(moment)
        print(f"\n--- Исполнение {moment:%d.%m %H:%M}, готовых операций ---")
        finished = processor.process_queue(queue)
        if not finished:
            print("  Готовых операций нет")
        for transaction in finished:
            records = [
                record
                for record in audit_log.records
                if record["transaction_id"] == transaction.transaction_id
            ]
            review = next(
                (record for record in records if record["risk"] is not None),
                None,
            )
            final = records[-1] if records else None
            risk = review["risk"].value if review else "-"
            message = final["message"] if final else transaction.rejection_reason
            if transaction.status == TransactionStatus.completed:
                mark = "ИСПОЛНЕНА"
            else:
                mark = "ОТКЛОНЕНА"
            print(f"  {mark:<10} {_describe(transaction)} | {risk:<6} | {message}")
            results.append(transaction)
        if queue.transactions:
            print("  Остались в очереди:")
            for waiting in queue.transactions:
                when = waiting.scheduled_at.strftime("%d.%m %H:%M")
                print(f"    {_describe(waiting)} до {when}")
        return finished

    print("\n--- Утро: обычные переводы и новые получатели ---")
    enqueue(transfer(boris_checking, anna_checking, 100), priority=5)
    enqueue(transfer(anna_checking, clara_checking, 120))
    enqueue(transfer(clara_checking, dmitry_checking, 90))
    enqueue(transfer(dmitry_checking, elena_checking, 70))
    enqueue(transfer(elena_checking, ivan_checking, 110))
    enqueue(transfer(ivan_checking, olga_checking, 60))
    enqueue(transfer(olga_checking, boris_checking, 40))
    enqueue(
        Transaction(TransactionType.deposit, 500, Currency.usd, recipient=anna_savings)
    )
    enqueue(
        Transaction(TransactionType.deposit, 200, Currency.usd, recipient=elena_checking)
    )
    enqueue(
        Transaction(TransactionType.withdraw, 80, Currency.usd, sender=clara_checking)
    )
    process_ready(datetime(2026, 10, 26, 10, 0))

    print("\n--- Повторные операции между знакомыми счетами ---")
    enqueue(transfer(anna_checking, clara_checking, 100))
    enqueue(transfer(boris_checking, anna_checking, 80))
    enqueue(transfer(elena_checking, ivan_checking, 50))
    enqueue(transfer(ivan_checking, olga_checking, 40))
    enqueue(transfer(clara_checking, dmitry_checking, 60))
    enqueue(transfer(clara_checking, clara_investment, 300))
    enqueue(
        Transaction(TransactionType.deposit, 300, Currency.usd, recipient=olga_checking)
    )
    enqueue(
        Transaction(TransactionType.withdraw, 30, Currency.usd, sender=dmitry_checking)
    )
    enqueue(transfer(anna_checking, anna_savings, 200))
    process_ready(datetime(2026, 10, 26, 11, 0))

    print("\n--- Ошибочные операции ---")
    clock.set(datetime(2026, 10, 26, 12, 0))
    bank.freeze_account(olga.client_id, "pass", olga_checking._account_id)
    bank.close_account(olga.client_id, "pass", olga_extra._account_id)
    enqueue(transfer(anna_savings, anna_checking, 100))
    enqueue(transfer(boris_premium, clara_checking, 50))
    enqueue(transfer(clara_investment, dmitry_checking, 100))
    process_ready(datetime(2026, 10, 26, 12, 0))
    enqueue(transfer(dmitry_checking, elena_checking, 50_000))
    enqueue(transfer(olga_checking, boris_checking, 25))
    enqueue(transfer(boris_checking, olga_checking, 30))
    enqueue(
        transfer(
            anna_savings,
            anna_checking,
            int(anna_savings._balance - anna_savings._min_balance + 50),
        )
    )
    enqueue(transfer(olga_extra, anna_checking, 25))
    enqueue(transfer(boris_premium, clara_checking, 50_000))
    enqueue(transfer(clara_investment, dmitry_checking, 50_000))
    process_ready(datetime(2026, 10, 26, 12, 10))

    print("\n--- Подозрительные, но разрешённые операции ---")
    enqueue(transfer(boris_checking, anna_checking, 2_000))
    enqueue(transfer(ivan_checking, elena_checking, 30))
    enqueue(transfer(ivan_checking, elena_checking, 30))
    enqueue(transfer(ivan_checking, elena_checking, 30))
    enqueue(transfer(elena_checking, dmitry_checking, 50))
    enqueue(
        Transaction(
            TransactionType.external,
            100,
            Currency.usd,
            sender=anna_checking,
            external_recipient="EXT-100",
        )
    )
    process_ready(datetime(2026, 10, 26, 13, 0))

    print("\n--- Ночные операции ---")
    enqueue(transfer(anna_checking, clara_checking, 70))
    process_ready(datetime(2026, 10, 27, 2, 0))
    enqueue(
        Transaction(
            TransactionType.external,
            100,
            Currency.usd,
            sender=anna_checking,
            external_recipient="EXT-900",
        )
    )
    process_ready(datetime(2026, 10, 27, 2, 20))
    enqueue(transfer(boris_checking, anna_checking, 1_800))
    process_ready(datetime(2026, 10, 27, 2, 40))
    enqueue(transfer(clara_checking, dmitry_checking, 40))
    process_ready(datetime(2026, 10, 27, 3, 10))

    print("\n--- День: приоритет и отложенные операции ---")
    enqueue(transfer(elena_checking, ivan_checking, 20))
    enqueue(transfer(dmitry_checking, clara_checking, 20))
    enqueue(transfer(ivan_checking, olga_checking, 20), priority=5)
    enqueue(transfer(anna_checking, boris_checking, 90))
    enqueue(transfer(ivan_premium, ivan_checking, 100))
    enqueue(transfer(elena_savings, elena_checking, 200))
    evening = enqueue(
        transfer(anna_checking, clara_checking, 15),
        scheduled_at=datetime(2026, 10, 27, 18, 0),
    )
    cancelled_later = enqueue(
        transfer(elena_checking, ivan_checking, 15),
        scheduled_at=datetime(2026, 10, 27, 23, 0),
    )
    print("Очередь до исполнения:")
    for waiting in queue.transactions:
        print(f"  {waiting.status.value:<10} {_describe(waiting)}")
    process_ready(datetime(2026, 10, 27, 16, 30))

    clock.set(datetime(2026, 10, 27, 16, 40))
    cancelled = queue.cancel(cancelled_later.transaction_id, now=clock.now())
    results.append(cancelled)
    print(f"  ОТМЕНЕНА   {_describe(cancelled)} | отмена клиентом")

    process_ready(datetime(2026, 10, 27, 18, 0))
    if evening.status != TransactionStatus.completed:
        raise RuntimeError("Отложенная транзакция не исполнилась в 18:00")

    print("\n=== Счета клиента ===")
    print(anna)
    for account in bank.search_accounts(client_id=anna.client_id):
        print(f"  {account}")

    print("\n=== История Анны Петровой ===")
    for record in audit_log.filter(actor="Anna Petrova"):
        moment = record["timestamp"].strftime("%d.%m %H:%M")
        print(
            f"  {moment} {record['level'].value:<8} "
            f"{record['transaction_type']:<8} {record['amount']} "
            f"{record['message']}"
        )

    print("\n=== Подозрительные операции ===")
    report = AuditReport(audit_log)
    suspicious = report.suspicious_operations()
    print(f"Всего: {len(suspicious)}")
    for record in suspicious:
        moment = record["timestamp"].strftime("%d.%m %H:%M")
        risk = record["risk"].value if record["risk"] is not None else "-"
        print(
            f"  {moment} {record['level'].value:<8} {risk:<6} "
            f"{record['actor']}: {record['message']}"
        )

    print("\n=== Топ-3 клиентов ===")
    for place, row in enumerate(bank.get_clients_ranking()[:3], start=1):
        print(
            f"  {place}. {row['full_name']}: {row['total_balance']} "
            f"({row['status'].value})"
        )

    print("\n=== Статистика транзакций ===")
    print(f"Всего создано: {len(results)}")
    for status in TransactionStatus:
        count = sum(1 for transaction in results if transaction.status == status)
        if count:
            print(f"  {status.value}: {count}")
    print("Ошибки и блокировки:", report.error_statistics())

    print("\n=== Общий баланс ===")
    for currency, amount in bank.get_total_balance().items():
        print(f"  {currency.value}: {amount}")

    if not 30 <= len(results) <= 50:
        raise RuntimeError(f"Ожидалось 30–50 транзакций, получено {len(results)}")


if __name__ == "__main__":
    run()
