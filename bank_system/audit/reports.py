from ..core.enums import AuditLevel, RiskLevel
from .audit_log import AuditLog


class AuditReport:
    def __init__(self, audit_log: AuditLog):
        if not isinstance(audit_log, AuditLog):
            raise ValueError("Incorrect audit log")

        self._audit_log = audit_log

    def suspicious_operations(self):
        return [
            record
            for record in self._audit_log.records
            if record["level"] in (AuditLevel.warning, AuditLevel.critical)
            or record.get("risk") in (RiskLevel.medium, RiskLevel.high)
        ]

    def client_risk_profile(self, actor: str):
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("Incorrect actor")

        records = [
            record
            for record in self._audit_log.filter(actor=actor)
            if record.get("risk") is not None
        ]
        counts = {
            RiskLevel.low: 0,
            RiskLevel.medium: 0,
            RiskLevel.high: 0,
        }
        for record in records:
            counts[record["risk"]] += 1

        if counts[RiskLevel.high]:
            level = RiskLevel.high
        elif counts[RiskLevel.medium]:
            level = RiskLevel.medium
        else:
            level = RiskLevel.low

        return {
            "actor": actor,
            "operations": len(records),
            "risk_counts": counts,
            "level": level,
        }

    def error_statistics(self):
        errors = [
            record
            for record in self._audit_log.records
            if record["level"] in (AuditLevel.error, AuditLevel.critical)
        ]
        by_message: dict[str, int] = {}
        for record in errors:
            by_message[record["message"]] = by_message.get(record["message"], 0) + 1

        return {
            "total": len(errors),
            "by_message": by_message,
        }
