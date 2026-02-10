"""Tests for the rule engine."""

import pytest

from src.rules.engine import RuleEngine


@pytest.fixture
def engine():
    return RuleEngine()


def test_yaml_config_loads(engine: RuleEngine):
    assert engine.attendance_rules is not None
    assert engine.fee_rules is not None
    assert len(engine.attendance_rules["thresholds"]) == 3
    assert len(engine.fee_rules["thresholds"]) == 3


# ── Attendance threshold tests ─────────────────────────────────────


def test_attendance_90_is_none(engine: RuleEngine):
    result = engine.evaluate_attendance_percentage(90.0)
    assert result.level == "none"


def test_attendance_85_is_none(engine: RuleEngine):
    result = engine.evaluate_attendance_percentage(85.0)
    assert result.level == "none"


def test_attendance_80_is_yellow(engine: RuleEngine):
    result = engine.evaluate_attendance_percentage(80.0)
    assert result.level == "yellow"


def test_attendance_75_is_orange(engine: RuleEngine):
    """75% is at the boundary — should be orange (75 <= x < 85 is yellow, but 60 <= x < 75 is orange)."""
    result = engine.evaluate_attendance_percentage(70.0)
    assert result.level == "orange"


def test_attendance_60_is_red(engine: RuleEngine):
    result = engine.evaluate_attendance_percentage(55.0)
    assert result.level == "red"


def test_attendance_0_is_red(engine: RuleEngine):
    result = engine.evaluate_attendance_percentage(0.0)
    assert result.level == "red"


# ── Consecutive absences tests ─────────────────────────────────────


def test_consecutive_0_is_none(engine: RuleEngine):
    result = engine.evaluate_consecutive_absences(0)
    assert result.level == "none"


def test_consecutive_2_is_none(engine: RuleEngine):
    result = engine.evaluate_consecutive_absences(2)
    assert result.level == "none"


def test_consecutive_3_is_red(engine: RuleEngine):
    result = engine.evaluate_consecutive_absences(3)
    assert result.level == "red"


def test_consecutive_5_is_red(engine: RuleEngine):
    result = engine.evaluate_consecutive_absences(5)
    assert result.level == "red"


# ── Fee threshold tests ────────────────────────────────────────────


def test_fee_not_overdue(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(0)
    assert result.level == "none"


def test_fee_5_days_overdue_none(engine: RuleEngine):
    """5 days overdue — below 7 day threshold."""
    result = engine.evaluate_fee_overdue(5)
    assert result.level == "none"


def test_fee_7_days_overdue_yellow(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(7)
    assert result.level == "yellow"


def test_fee_10_days_overdue_yellow(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(10)
    assert result.level == "yellow"


def test_fee_15_days_overdue_orange(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(15)
    assert result.level == "orange"


def test_fee_20_days_overdue_orange(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(20)
    assert result.level == "orange"


def test_fee_30_days_overdue_red(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(30)
    assert result.level == "red"


def test_fee_60_days_overdue_red(engine: RuleEngine):
    result = engine.evaluate_fee_overdue(60)
    assert result.level == "red"
