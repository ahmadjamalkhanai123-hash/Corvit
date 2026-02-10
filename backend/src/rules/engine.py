"""Rule engine that loads rules.yaml and evaluates student data."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AlertResult:
    level: str  # "yellow", "orange", "red", or "none"
    message: str
    details: dict[str, Any] | None = None


class RuleEngine:
    """Loads rules from YAML config and evaluates data against thresholds."""

    def __init__(self, rules_path: str | None = None):
        if rules_path is None:
            rules_path = str(Path(__file__).parent.parent / "config" / "rules.yaml")
        with open(rules_path) as f:
            self._rules = yaml.safe_load(f)

    @property
    def attendance_rules(self) -> dict:
        return self._rules.get("attendance", {})

    @property
    def fee_rules(self) -> dict:
        return self._rules.get("fees", {})

    def evaluate_attendance_percentage(self, percentage: float) -> AlertResult:
        """Evaluate attendance percentage against thresholds."""
        for threshold in self.attendance_rules.get("thresholds", []):
            min_pct = threshold["min_percentage"]
            max_pct = threshold["max_percentage"]
            if min_pct <= percentage < max_pct:
                return AlertResult(
                    level=threshold["level"],
                    message=threshold["message"],
                    details={"percentage": percentage},
                )
        if percentage >= 85:
            return AlertResult(level="none", message="Attendance is satisfactory.")
        return AlertResult(level="red", message="Attendance critically low.", details={"percentage": percentage})

    def evaluate_consecutive_absences(self, consecutive_count: int) -> AlertResult:
        """Evaluate consecutive absences against threshold."""
        rule = self.attendance_rules.get("consecutive_absences", {})
        threshold = rule.get("threshold", 3)
        if consecutive_count >= threshold:
            return AlertResult(
                level=rule.get("level", "red"),
                message=rule.get("message", f"{consecutive_count} consecutive absences."),
                details={"consecutive_absences": consecutive_count},
            )
        return AlertResult(level="none", message="No consecutive absence alert.")

    def evaluate_fee_overdue(self, days_overdue: int) -> AlertResult:
        """Evaluate fee overdue days against thresholds."""
        if days_overdue <= 0:
            return AlertResult(level="none", message="Fee is not overdue.")
        result = AlertResult(level="none", message="Fee is not overdue.")
        for threshold in self.fee_rules.get("thresholds", []):
            min_days = threshold["days_overdue"]
            max_days = threshold.get("max_days_overdue")
            if max_days is None:
                if days_overdue >= min_days:
                    result = AlertResult(
                        level=threshold["level"],
                        message=threshold["message"],
                        details={"days_overdue": days_overdue},
                    )
            elif min_days <= days_overdue < max_days:
                result = AlertResult(
                    level=threshold["level"],
                    message=threshold["message"],
                    details={"days_overdue": days_overdue},
                )
        return result
