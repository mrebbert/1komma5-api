"""ChargingMode accepts values the vendor adds without a library release."""

import pytest

from onekommafive.models import ChargingMode


def test_known_values_map_to_their_members() -> None:
    assert ChargingMode("SMART_CHARGE") is ChargingMode.SMART_CHARGE
    assert ChargingMode("PROGRAM_CHARGE") is ChargingMode.PROGRAM_CHARGE


def test_unknown_value_becomes_a_member_with_that_value() -> None:
    mode = ChargingMode("FUTURE_CHARGE")
    assert mode.value == "FUTURE_CHARGE"
    assert mode.name == "FUTURE_CHARGE"
    assert str(mode) == "FUTURE_CHARGE"
    assert isinstance(mode, ChargingMode)


def test_unknown_value_is_cached_and_compares_by_value() -> None:
    assert ChargingMode("FUTURE_CHARGE") is ChargingMode("FUTURE_CHARGE")
    assert ChargingMode("FUTURE_CHARGE") == "FUTURE_CHARGE"
    assert ChargingMode("FUTURE_CHARGE") != ChargingMode.SOLAR_CHARGE


def test_unknown_values_stay_out_of_the_listed_members() -> None:
    ChargingMode("FUTURE_CHARGE")
    assert [m.value for m in ChargingMode] == [
        "SMART_CHARGE",
        "QUICK_CHARGE",
        "SOLAR_CHARGE",
        "PROGRAM_CHARGE",
    ]


@pytest.mark.parametrize("bad", ["", None, 3])
def test_empty_or_non_string_still_raises(bad: object) -> None:
    with pytest.raises(ValueError):
        ChargingMode(bad)
