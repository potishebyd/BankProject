import csv
import json
from datetime import datetime
from pathlib import Path

from ..audit.audit_log import AuditLog
from ..audit.reports import AuditReport
from ..banking.bank import Bank
from ..core.enums import AccountStatus, AuditLevel, RiskLevel


class ReportBuilder:
    def __init__(self, bank: Bank, audit_log: AuditLog):
        if not isinstance(bank, Bank):
            raise ValueError("Incorrect bank")
        if not isinstance(audit_log, AuditLog):
            raise ValueError("Incorrect audit log")

        self._bank = bank
        self._audit_log = audit_log
        self._audit_report = AuditReport(audit_log)

    def client_report(self, actor: str) -> dict:
        client = self._find_client(actor)
        balances = self._balances_by_currency(client["client_id"])
        accounts = []
        for account in self._bank.search_accounts(client_id=client["client_id"]):
            info = account.get_account_info()
            accounts.append(
                {
                    "account_id": info["account_id"],
                    "type": type(account).__name__,
                    "status": info["status"].value,
                    "balance": info.get("total_value", info["balance"]),
                    "currency": info["currency"].value,
                }
            )

        profile = self._audit_report.client_risk_profile(actor)
        history = []
        for record in self._audit_log.filter(actor=actor):
            history.append(self._history_row(record))

        return {
            "report_type": "client",
            "title": f"Client report: {actor}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "client": actor,
                "status": client["status"].value,
                "accounts": len(accounts),
                "balances": self._format_balances(balances),
                "operations": profile["operations"],
                "risk_level": profile["level"].value,
                "low": profile["risk_counts"][RiskLevel.low],
                "medium": profile["risk_counts"][RiskLevel.medium],
                "high": profile["risk_counts"][RiskLevel.high],
            },
            "accounts": accounts,
            "rows": history,
        }

    def bank_report(self) -> dict:
        ranking = self._bank.get_clients_ranking()
        balances = {
            currency.value: amount
            for currency, amount in self._bank.get_total_balance().items()
        }
        rows = []
        for row in ranking:
            rows.append(
                {
                    "client": row["full_name"],
                    "status": row["status"].value,
                    "total_balance": row["total_balance"],
                    "accounts": len(
                        self._bank.search_accounts(client_id=row["client_id"])
                    ),
                }
            )

        account_count = sum(row["accounts"] for row in rows)
        return {
            "report_type": "bank",
            "title": f"Bank report: {self._bank.name}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "bank": self._bank.name,
                "clients": len(ranking),
                "accounts": account_count,
                "balances": self._format_balances(balances),
                "operations": len(self._review_records()),
                "suspicious": len(self._audit_report.suspicious_operations()),
            },
            "rows": rows,
        }

    def risk_report(self) -> dict:
        counts = {level.value: 0 for level in RiskLevel}
        for record in self._review_records():
            counts[record["risk"].value] += 1

        rows = []
        for record in self._audit_report.suspicious_operations():
            rows.append(
                {
                    "timestamp": self._format_time(record["timestamp"]),
                    "actor": record["actor"],
                    "risk": record["risk"].value if record["risk"] else "",
                    "level": record["level"].value,
                    "message": record["message"],
                }
            )

        errors = self._audit_report.error_statistics()
        return {
            "report_type": "risk",
            "title": f"Risk report: {self._bank.name}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "low": counts["LOW"],
                "medium": counts["MEDIUM"],
                "high": counts["HIGH"],
                "suspicious": len(rows),
                "errors": errors["total"],
            },
            "rows": rows,
        }

    def to_text(self, report: dict) -> str:
        lines = [
            report["title"],
            "=" * len(report["title"]),
            f"Generated: {report['generated_at']}",
            "",
        ]
        for key, value in report["summary"].items():
            lines.append(f"{key}: {value}")

        accounts = report.get("accounts") or []
        if accounts:
            lines.extend(["", "Accounts:"])
            for account in accounts:
                lines.append(
                    f"  {account['account_id']} {account['type']} "
                    f"{account['status']} {account['balance']} {account['currency']}"
                )

        rows = report["rows"]
        lines.append("")
        if not rows:
            lines.append("No rows")
            return "\n".join(lines)

        headers = list(rows[0].keys())
        lines.append(" | ".join(headers))
        for row in rows:
            lines.append(" | ".join(str(row.get(header, "")) for header in headers))
        return "\n".join(lines)

    def export_to_json(self, report: dict, file_path: str) -> Path:
        path = self._prepare_path(file_path)
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def export_to_csv(self, report: dict, file_path: str) -> Path:
        path = self._prepare_path(file_path)
        rows = report["rows"]
        with path.open("w", encoding="utf-8", newline="") as file:
            if not rows:
                file.write("")
                return path
            writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def save_charts(self, directory: str) -> dict[str, Path]:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        paths = {
            "pie": folder / "risk_pie.png",
            "bar": folder / "client_balances.png",
            "flow": folder / "balance_flow.png",
        }
        self._save_risk_pie(plt, paths["pie"])
        self._save_balance_bars(plt, paths["bar"])
        self._save_balance_flow(plt, paths["flow"])
        return paths

    def _save_risk_pie(self, plt, path: Path):
        counts = {level.value: 0 for level in RiskLevel}
        for record in self._review_records():
            counts[record["risk"].value] += 1

        labels = [label for label, count in counts.items() if count]
        sizes = [counts[label] for label in labels]
        figure, axis = plt.subplots(figsize=(6, 6))
        if sizes:
            axis.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90)
        else:
            axis.text(0.5, 0.5, "No operations", ha="center", va="center")
            axis.axis("off")
        axis.set_title("Risk distribution")
        figure.tight_layout()
        figure.savefig(path, dpi=120)
        plt.close(figure)

    def _save_balance_bars(self, plt, path: Path):
        ranking = self._bank.get_clients_ranking()
        names = [row["full_name"] for row in ranking]
        balances = [row["total_balance"] for row in ranking]
        figure, axis = plt.subplots(figsize=(8, 4.5))
        if names:
            axis.bar(names, balances)
            axis.tick_params(axis="x", rotation=20)
        else:
            axis.text(0.5, 0.5, "No clients", ha="center", va="center")
        axis.set_title("Client balances")
        axis.set_ylabel("Balance")
        figure.tight_layout()
        figure.savefig(path, dpi=120)
        plt.close(figure)

    def _save_balance_flow(self, plt, path: Path):
        series = self._cash_flow()
        figure, axis = plt.subplots(figsize=(8, 4.5))
        if not series:
            axis.text(0.5, 0.5, "No completed operations", ha="center", va="center")
        for actor, points in series.items():
            axis.plot(
                range(len(points)),
                [point["cumulative"] for point in points],
                marker="o",
                label=actor,
            )
        axis.set_title("Balance movement")
        axis.set_xlabel("Completed operation")
        axis.set_ylabel("Cumulative flow")
        if series:
            axis.legend()
        figure.tight_layout()
        figure.savefig(path, dpi=120)
        plt.close(figure)

    def _cash_flow(self):
        cumulative = {}
        series = {}
        for record in self._audit_log.records:
            if record.get("risk") is None:
                continue
            if not self._money_moved(record["transaction_id"]):
                continue

            actor = record["actor"] or "Unknown"
            amount = record["amount"] or 0
            if record["transaction_type"] == "DEPOSIT":
                delta = amount
            else:
                delta = -amount

            cumulative[actor] = cumulative.get(actor, 0) + delta
            series.setdefault(actor, [{"step": 0, "cumulative": 0}])
            series[actor].append(
                {
                    "step": len(series[actor]),
                    "cumulative": cumulative[actor],
                }
            )
        return series

    def _money_moved(self, transaction_id: str) -> bool:
        records = [
            record
            for record in self._audit_log.records
            if record["transaction_id"] == transaction_id
        ]
        return not any(
            record["level"] in (AuditLevel.error, AuditLevel.critical)
            for record in records
        )

    def _review_records(self):
        return [
            record
            for record in self._audit_log.records
            if record.get("risk") is not None
        ]

    def _find_client(self, actor: str):
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("Incorrect client name")

        for row in self._bank.get_clients_ranking():
            if row["full_name"] == actor:
                return row
        raise ValueError("Client not found")

    def _balances_by_currency(self, client_id: str):
        totals = {}
        for account in self._bank.search_accounts(client_id=client_id):
            info = account.get_account_info()
            if info["status"] == AccountStatus.closed:
                continue
            currency = info["currency"].value
            value = info.get("total_value", info["balance"])
            totals[currency] = totals.get(currency, 0) + value
        return totals

    @staticmethod
    def _format_balances(balances: dict) -> str:
        if not balances:
            return "0"
        return ", ".join(
            f"{currency}: {amount}" for currency, amount in balances.items()
        )

    @staticmethod
    def _format_time(value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _history_row(record: dict) -> dict:
        return {
            "timestamp": record["timestamp"].strftime("%Y-%m-%d %H:%M"),
            "type": record["transaction_type"],
            "amount": record["amount"],
            "currency": record["currency"],
            "level": record["level"].value,
            "risk": record["risk"].value if record["risk"] else "",
            "message": record["message"],
        }

    @staticmethod
    def _prepare_path(file_path: str) -> Path:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("Incorrect report path")
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
