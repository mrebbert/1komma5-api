"""Tests for :mod:`onekommafive.ev_charger` – EV charger read and control."""

from __future__ import annotations

from unittest.mock import MagicMock

import responses as resp_lib
import pytest

from onekommafive.errors import RequestError
from onekommafive.ev_charger import EVCharger
from onekommafive.models import ChargingMode
from tests.fixtures import (
    FAKE_CHARGER_ID,
    FAKE_EV_ID,
    FAKE_SYSTEM_ID,
    make_client,
    make_ev_data,
    make_system_data,
)

_BASE_URL = (
    f"https://heartbeat.1komma5grad.com/api/v1/systems/{FAKE_SYSTEM_ID}/devices/evs/{FAKE_EV_ID}"
)


def _make_charger(
    charging_mode: str = "SMART_CHARGE",
    manual_soc: float | None = 0.8,
) -> EVCharger:
    """Return an :class:`EVCharger` instance backed by mocked dependencies."""
    client = make_client()

    # Minimal system mock – only id() is required by EVCharger
    system = MagicMock()
    system.id.return_value = FAKE_SYSTEM_ID

    data = make_ev_data(FAKE_EV_ID, charging_mode, manual_soc)
    return EVCharger(client, system, data)


# ---------------------------------------------------------------------------
# Read-only properties
# ---------------------------------------------------------------------------

class TestEvChargerProperties:
    """Tests for read-only accessor methods."""

    def test_id_returns_correct_value(self) -> None:
        charger = _make_charger()
        assert charger.id() == FAKE_EV_ID

    def test_name_returns_profile_name(self) -> None:
        charger = _make_charger()
        assert charger.name() == "My Car"

    def test_name_returns_none_when_no_profile(self) -> None:
        client = make_client()
        system = MagicMock()
        system.id.return_value = FAKE_SYSTEM_ID
        data = {"id": FAKE_EV_ID, "chargeSettings": {"chargingMode": "QUICK_CHARGE"}}
        charger = EVCharger(client, system, data)
        assert charger.name() is None

    def test_charging_mode_returns_enum(self) -> None:
        charger = _make_charger(charging_mode="SMART_CHARGE")
        assert charger.charging_mode() == ChargingMode.SMART_CHARGE

    def test_repr_contains_id_and_mode(self) -> None:
        charger = _make_charger()
        r = repr(charger)
        assert FAKE_EV_ID in r
        assert "SMART_CHARGE" in r

    def test_manufacturer_strips_whitespace(self) -> None:
        charger = _make_charger()
        assert charger.manufacturer() == "Volkswagen"

    def test_model_returns_model_name(self) -> None:
        assert _make_charger().model() == "Id.4"

    def test_capacity_wh_returns_float(self) -> None:
        assert _make_charger().capacity_wh() == pytest.approx(77000.0)

    def test_min_charging_current_a(self) -> None:
        assert _make_charger().min_charging_current_a() == pytest.approx(2.0)

    def test_safety_range_km(self) -> None:
        assert _make_charger().safety_range_km() == pytest.approx(0.0)

    def test_assigned_charger_id(self) -> None:
        assert _make_charger().assigned_charger_id() == FAKE_CHARGER_ID

    def test_manual_soc_timestamp(self) -> None:
        assert _make_charger().manual_soc_timestamp() == "2026-02-27T17:49:55.213Z"

    def test_updated_at(self) -> None:
        assert _make_charger().updated_at() == "2026-02-28T07:35:39.367Z"

    def test_charging_mode_updated_at(self) -> None:
        assert _make_charger().charging_mode_updated_at() == "2026-02-28T07:35:39.367Z"

    def test_default_soc_as_percentage(self) -> None:
        assert _make_charger().default_soc() == pytest.approx(35.0)

    def test_target_soc_as_percentage(self) -> None:
        assert _make_charger().target_soc() == pytest.approx(80.0)

    def test_primary_schedule_days_empty_list(self) -> None:
        assert _make_charger().primary_schedule_days() == []

    def test_primary_schedule_departure_time(self) -> None:
        assert _make_charger().primary_schedule_departure_time() == "12:00"

    def test_primary_schedule_departure_soc_as_percentage(self) -> None:
        assert _make_charger().primary_schedule_departure_soc() == pytest.approx(100.0)

    def test_secondary_schedule_fields_none_when_not_set(self) -> None:
        charger = _make_charger()
        assert charger.secondary_schedule_departure_time() is None
        assert charger.secondary_schedule_departure_soc() is None

    def test_manufacturer_none_when_profile_absent(self) -> None:
        client = make_client()
        system = MagicMock()
        system.id.return_value = FAKE_SYSTEM_ID
        data = {"id": FAKE_EV_ID, "chargeSettings": {"chargingMode": "QUICK_CHARGE"}}
        charger = EVCharger(client, system, data)
        assert charger.manufacturer() is None
        assert charger.capacity_wh() is None


# ---------------------------------------------------------------------------
# current_soc
# ---------------------------------------------------------------------------

class TestCurrentSoc:
    """Tests for EVCharger.current_soc."""

    def test_returns_percentage_when_smart_charge_and_soc_set(self) -> None:
        charger = _make_charger(charging_mode="SMART_CHARGE", manual_soc=0.75)
        assert charger.current_soc() == pytest.approx(75.0)

    def test_returns_none_when_not_smart_charge(self) -> None:
        charger = _make_charger(charging_mode="QUICK_CHARGE", manual_soc=0.75)
        assert charger.current_soc() is None

    def test_returns_none_when_no_manual_soc(self) -> None:
        charger = _make_charger(charging_mode="SMART_CHARGE", manual_soc=None)
        assert charger.current_soc() is None

    def test_zero_soc_returns_zero_percent(self) -> None:
        charger = _make_charger(charging_mode="SMART_CHARGE", manual_soc=0.0)
        assert charger.current_soc() == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# set_charging_mode
# ---------------------------------------------------------------------------

class TestSetChargingMode:
    """Tests for EVCharger.set_charging_mode."""

    @resp_lib.activate
    def test_sends_patch_request_with_new_mode(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={}, status=200)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        charger.set_charging_mode(ChargingMode.QUICK_CHARGE)

        import json
        body = json.loads(resp_lib.calls[0].request.body)
        assert body["chargeSettings"]["chargingMode"] == "QUICK_CHARGE"

    @resp_lib.activate
    def test_updates_internal_state_after_success(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={}, status=200)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        charger.set_charging_mode(ChargingMode.SOLAR_CHARGE)

        assert charger.charging_mode() == ChargingMode.SOLAR_CHARGE

    def test_no_op_when_mode_unchanged(self) -> None:
        """No HTTP call should be made when the requested mode matches current mode."""
        charger = _make_charger(charging_mode="SMART_CHARGE")
        # If a request were made, responses would raise ConnectionError (no mock registered)
        charger.set_charging_mode(ChargingMode.SMART_CHARGE)

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={"error": "error"}, status=400)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        with pytest.raises(RequestError, match="Failed to set charging mode"):
            charger.set_charging_mode(ChargingMode.QUICK_CHARGE)


# ---------------------------------------------------------------------------
# set_current_soc
# ---------------------------------------------------------------------------

class TestSetCurrentSoc:
    """Tests for EVCharger.set_current_soc."""

    @resp_lib.activate
    def test_sends_patch_with_decimal_soc(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={}, status=200)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        charger.set_current_soc(80.0)

        import json
        body = json.loads(resp_lib.calls[0].request.body)
        assert body["manualSoc"] == pytest.approx(0.8)

    @resp_lib.activate
    def test_sends_zero_when_soc_is_zero(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={}, status=200)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        charger.set_current_soc(0.0)

        import json
        body = json.loads(resp_lib.calls[0].request.body)
        assert body["manualSoc"] == pytest.approx(0.0)

    def test_no_op_when_not_smart_charge(self) -> None:
        """set_current_soc must be silent when the charger is not in SMART_CHARGE mode."""
        charger = _make_charger(charging_mode="QUICK_CHARGE")
        # Would raise ConnectionError if HTTP call were attempted
        charger.set_current_soc(80.0)

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.PATCH, _BASE_URL, json={"error": "bad request"}, status=400)

        charger = _make_charger(charging_mode="SMART_CHARGE")
        with pytest.raises(RequestError, match="Failed to set state of charge"):
            charger.set_current_soc(60.0)
