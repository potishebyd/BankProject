import json
from datetime import datetime
from pathlib import Path

from ..core.enums import AuditLevel, RiskLevel


class AuditLog:
    def __init__(
        self,
        file_path: str | None = None,
        now_func=datetime.now,
        restore: bool = False,
    ):
        if file_path is not None and (not isinstance(file_path, str) or not file_path.strip()):
            raise ValueError("Incorrect audit file path")

        self._file_path = file_path
        self._now = now_func
        self._records: list[dict] = []

        if file_path is None:
            return

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if restore:
            self.load()
        else:
            path.write_text("", encoding="utf-8")

    @property
    def records(self):
        return list(self._records)

    @property
    def file_path(self):
        return self._file_path

    def record(
        self,
        level: AuditLevel,
        message: str,
        actor: str | None = None,
        account_id: str | None = None,
        transaction_id: str | None = None,
        transaction_type: str | None = None,
        amount: int | float | None = None,
        currency: str | None = None,
        risk: RiskLevel | None = None,
        reasons: list[str] | None = None,
    ):
        if not isinstance(level, AuditLevel):
            raise ValueError("Incorrect audit level")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Incorrect audit message")

        if risk is not None and not isinstance(risk, RiskLevel):
            raise ValueError("Incorrect risk level")

        entry = {
            "timestamp": self._now(),
            "level": level,
            "message": message,
            "actor": actor,
            "account_id": account_id,
            "transaction_id": transaction_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "currency": currency,
            "risk": risk,
            "reasons": list(reasons or []),
        }
        self._records.append(entry)
        self._append_to_file(entry)
        return entry

    def filter(
        self,
        level: AuditLevel | None = None,
        actor: str | None = None,
        risk: RiskLevel | None = None,
        query: str | None = None,
    ):
        if level is not None and not isinstance(level, AuditLevel):
            raise ValueError("Incorrect audit level")

        if risk is not None and not isinstance(risk, RiskLevel):
            raise ValueError("Incorrect risk level")

        found = self._records

        if level is not None:
            found = [item for item in found if item["level"] == level]

        if actor is not None:
            found = [item for item in found if item["actor"] == actor]

        if risk is not None:
            found = [item for item in found if item["risk"] == risk]

        if query:
            needle = query.lower()
            found = [
                item
                for item in found
                if needle in item["message"].lower()
                or needle in " ".join(item["reasons"]).lower()
            ]

        return list(found)

    def load(self):
        self._records = []
        if self._file_path is None:
            return self.records

        path = Path(self._file_path)
        if not path.exists():
            return self.records

        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            self._records.append(self._from_payload(json.loads(line)))

        return self.records

    def _append_to_file(self, entry: dict):
        if self._file_path is None:
            return

        with Path(self._file_path).open("a", encoding="utf-8") as file:
            file.write(json.dumps(self._to_payload(entry), ensure_ascii=False))
            file.write("\n")

    @staticmethod
    def _enum_by_value(enum_cls, value):
        if value is None:
            return None

        for item in enum_cls:
            if item.value == value:
                return item

        raise ValueError(f"Unknown value {value}")

    def _to_payload(self, entry: dict):
        return {
            "timestamp": entry["timestamp"].isoformat(),
            "level": entry["level"].value,
            "message": entry["message"],
            "actor": entry["actor"],
            "account_id": entry["account_id"],
            "transaction_id": entry["transaction_id"],
            "transaction_type": entry["transaction_type"],
            "amount": entry["amount"],
            "currency": entry["currency"],
            "risk": entry["risk"].value if entry["risk"] is not None else None,
            "reasons": entry["reasons"],
        }

    def _from_payload(self, payload: dict):
        return {
            "timestamp": datetime.fromisoformat(payload["timestamp"]),
            "level": self._enum_by_value(AuditLevel, payload["level"]),
            "message": payload["message"],
            "actor": payload["actor"],
            "account_id": payload["account_id"],
            "transaction_id": payload["transaction_id"],
            "transaction_type": payload["transaction_type"],
            "amount": payload["amount"],
            "currency": payload["currency"],
            "risk": self._enum_by_value(RiskLevel, payload["risk"]),
            "reasons": list(payload["reasons"]),
        }
