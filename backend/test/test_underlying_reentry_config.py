import pytest
from pydantic import ValidationError

from backend.schemas.strategy_module import Leg
from backend.strategy.tick_processor import _compare_trigger


def _base_option_leg(**overrides):
    data = {
        "id": 1,
        "segment": "options",
        "expiry": "current_month",
        "lots": 1,
        "position": "S",
        "option_type": "CE",
        "strike_mode": "atm",
        "atm_offset": "ATM",
        "target_pts": None,
        "sl_pts": 10,
        "trail": {"x": 0, "y": 0},
    }
    data.update(overrides)
    return data


def test_leg_accepts_underlying_entry_risk_and_reentry_config():
    leg = Leg.model_validate(_base_option_leg(
        underlying_entry={"operator": "is_above", "value": 22600},
        underlying_risk={"sl_pts": 50, "target_pts": 100},
        reentry={"mode": "reexecute", "max_count": 2, "on": "sl_or_target"},
    ))

    assert leg.underlying_entry is not None
    assert leg.underlying_entry.operator == "is_above"
    assert leg.underlying_risk is not None
    assert leg.underlying_risk.target_pts == 100
    assert leg.reentry is not None
    assert leg.reentry.mode == "reexecute"


def test_leg_rejects_unknown_underlying_operator():
    with pytest.raises(ValidationError):
        Leg.model_validate(_base_option_leg(
            underlying_entry={"operator": "crosses_above", "value": 22600},
        ))


@pytest.mark.parametrize(
    ("operator", "ltp", "value", "expected"),
    [
        ("is_above", 101, 100, True),
        ("is_above", 100, 100, False),
        ("is_below", 99, 100, True),
        ("equal_or_above", 100, 100, True),
        ("equal_or_below", 100, 100, True),
        ("equal_to", 100, 100, True),
        ("equal_to", 101, 100, False),
    ],
)
def test_compare_underlying_trigger(operator, ltp, value, expected):
    assert _compare_trigger(ltp, operator, value) is expected
