"""Tests for :mod:`onekommafive.ev_charger` – EV charger read and control."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aioresponses import aioresponses
from yarl import URL as _URL

from onekommafive.errors import RequestError
from onekommafive.ev_charger import EVCharger
from onekommafive.models import ChargingMode
from tests.fixtures import (
    FAKE_CHARGER_ID,
    FAKE_EV_ID,
    FAKE_SYSTEM_ID,
    make_client,
    make_ev_data,
)

_BASE_URL = f"https://heartbeat.1komma5grad.com/api/v2/sites/{FAKE_SYSTEM_ID}/assets/evs/{FAKE_EV_ID}"


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


def _patch_body(m: aioresponses) -> dict:
    """Return the JSON body of the most recent PATCH to ``_BASE_URL``."""
    calls = m.requests[("PATCH", _URL(_BASE_URL))]
    return calls[-1].kwargs["json"]


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

    def test_name_returns_none_when_absent(self) -> None:
        client = make_client()
        system = MagicMock()
        system.id.return_value = FAKE_SYSTEM_ID
        data = {"id": FAKE_EV_ID, "chargingMode": "QUICK_CHARGE"}
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

    def test_safety_range_km_returns_none_on_site_scoped(self) -> None:
        """v0.2.0+: site-scoped v2 API dropped the safety-range field."""
        assert _make_charger().safety_range_km() is None

    def test_assigned_charger_id(self) -> None:
        assert _make_charger().assigned_charger_id() == FAKE_CHARGER_ID

    def test_manual_soc_timestamp(self) -> None:
        assert _make_charger().manual_soc_timestamp() == "2026-02-27T17:49:55.213Z"

    def test_updated_at_returns_none_on_site_scoped(self) -> None:
        """v0.2.0+: site-scoped v2 API dropped the top-level updatedAt field."""
        assert _make_charger().updated_at() is None

    def test_charging_mode_updated_at_returns_none_on_site_scoped(self) -> None:
        """v0.2.0+: site-scoped v2 API dropped the chargingModeUpdatedAt field."""
        assert _make_charger().charging_mode_updated_at() is None

    def test_default_soc_as_percentage(self) -> None:
        assert _make_charger().default_soc() == pytest.approx(35.0)

    def test_target_soc_as_percentage(self) -> None:
        assert _make_charger().target_soc() == pytest.approx(80.0)

    def test_primary_schedule_days_empty_list(self) -> None:
        """v0.2.0+: site-scoped v2 API dropped the primary-schedule-days
        field; SDK returns an empty list."""
        assert _make_charger().primary_schedule_days() == []

    def test_primary_schedule_departure_time(self) -> None:
        assert _make_charger().primary_schedule_departure_time() == "12:00"

    def test_primary_schedule_departure_soc_aliases_target_soc(self) -> None:
        """v0.2.0+: v2 API consolidated the primary-schedule-departure-SoC
        and targetSoc into a single value. The SDK fallback returns
        target_soc() so HA sensors keep working with correct semantics."""
        charger = _make_charger()
        assert charger.primary_schedule_departure_soc() == charger.target_soc()
        assert charger.primary_schedule_departure_soc() == pytest.approx(80.0)

    def test_secondary_schedule_fields_none_on_site_scoped(self) -> None:
        """v0.2.0+: site-scoped v2 API dropped both secondary-schedule fields."""
        charger = _make_charger()
        assert charger.secondary_schedule_departure_time() is None
        assert charger.secondary_schedule_departure_soc() is None

    def test_capacity_wh_normalizes_kwh_unit(self) -> None:
        """Enphase-style users get capacity in kWh; SDK normalises to Wh."""
        client = make_client()
        system = MagicMock()
        system.id.return_value = FAKE_SYSTEM_ID
        data = make_ev_data(capacity_unit="kWh")
        charger = EVCharger(client, system, data)
        assert charger.capacity_wh() == pytest.approx(77000.0)

    def test_manufacturer_and_capacity_none_when_fields_absent(self) -> None:
        client = make_client()
        system = MagicMock()
        system.id.return_value = FAKE_SYSTEM_ID
        data = {"id": FAKE_EV_ID, "chargingMode": "QUICK_CHARGE"}
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

    async def test_sends_patch_request_with_new_mode(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            await charger.set_charging_mode(ChargingMode.QUICK_CHARGE)

            assert _patch_body(m) == {"chargingMode": "QUICK_CHARGE"}
            await charger._client.close()

    async def test_updates_internal_state_after_success(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            await charger.set_charging_mode(ChargingMode.SOLAR_CHARGE)

            assert charger.charging_mode() == ChargingMode.SOLAR_CHARGE
            await charger._client.close()

    async def test_no_op_when_mode_unchanged(self) -> None:
        """No HTTP call should be made when the requested mode matches current mode."""
        charger = _make_charger(charging_mode="SMART_CHARGE")
        # If a request were made, aioresponses would raise ConnectionError (no mock registered)
        await charger.set_charging_mode(ChargingMode.SMART_CHARGE)
        await charger._client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={"error": "error"}, status=400)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            with pytest.raises(RequestError, match="Failed to set charging mode"):
                await charger.set_charging_mode(ChargingMode.QUICK_CHARGE)
            await charger._client.close()


# ---------------------------------------------------------------------------
# set_current_soc
# ---------------------------------------------------------------------------


class TestSetCurrentSoc:
    """Tests for EVCharger.set_current_soc."""

    async def test_sends_patch_with_decimal_soc(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            await charger.set_current_soc(80.0)

            body = _patch_body(m)
            assert body["manualSoc"] == pytest.approx(0.8)
            await charger._client.close()

    async def test_sends_zero_when_soc_is_zero(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            await charger.set_current_soc(0.0)

            body = _patch_body(m)
            assert body["manualSoc"] == pytest.approx(0.0)
            await charger._client.close()

    async def test_no_op_when_not_smart_charge(self) -> None:
        """set_current_soc must be silent when the charger is not in SMART_CHARGE mode."""
        charger = _make_charger(charging_mode="QUICK_CHARGE")
        # Would raise ConnectionError if HTTP call were attempted
        await charger.set_current_soc(80.0)
        await charger._client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={"error": "bad request"}, status=400)

            charger = _make_charger(charging_mode="SMART_CHARGE")
            with pytest.raises(RequestError, match="Failed to set state of charge"):
                await charger.set_current_soc(60.0)
            await charger._client.close()


# ---------------------------------------------------------------------------
# set_target_soc
# ---------------------------------------------------------------------------


class TestSetTargetSoc:
    """Tests for EVCharger.set_target_soc."""

    async def test_sends_patch_with_decimal_soc(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.set_target_soc(90.0)

            body = _patch_body(m)
            assert body == {"targetSoc": pytest.approx(0.9)}
            await charger._client.close()

    async def test_updates_internal_state_after_success(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.set_target_soc(90.0)

            assert charger.target_soc() == pytest.approx(90.0)
            await charger._client.close()

    async def test_no_op_when_target_unchanged(self) -> None:
        charger = _make_charger()  # fixture target_soc = 80 %
        await charger.set_target_soc(80.0)  # no HTTP call expected
        await charger._client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={"error": "bad request"}, status=400)

            charger = _make_charger()
            with pytest.raises(
                RequestError, match="Failed to set target state of charge"
            ):
                await charger.set_target_soc(90.0)
            await charger._client.close()


# ---------------------------------------------------------------------------
# set_primary_departure_time
# ---------------------------------------------------------------------------


class TestSetPrimaryDepartureTime:
    """Tests for EVCharger.set_primary_departure_time."""

    async def test_sends_patch_with_time_string(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.set_primary_departure_time("07:30")

            assert _patch_body(m) == {"departureTime": "07:30"}
            await charger._client.close()

    async def test_updates_internal_state_after_success(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.set_primary_departure_time("07:30")

            assert charger.primary_schedule_departure_time() == "07:30"
            await charger._client.close()

    async def test_no_op_when_time_unchanged(self) -> None:
        charger = _make_charger()  # fixture departure time = "12:00"
        await charger.set_primary_departure_time("12:00")  # no HTTP call expected
        await charger._client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={"error": "bad request"}, status=400)

            charger = _make_charger()
            with pytest.raises(RequestError, match="Failed to set departure time"):
                await charger.set_primary_departure_time("07:30")
            await charger._client.close()


class TestAssignCharger:
    """Tests for EVCharger.assign_charger."""

    _NEW_CHARGER_ID = "cccccccc-0000-0000-0000-000000000099"

    async def test_sends_patch_with_charger_id(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.assign_charger(self._NEW_CHARGER_ID)

            # The URL is the key in m.requests, so a match there confirms it.
            assert ("PATCH", _URL(_BASE_URL)) in m.requests
            assert _patch_body(m) == {"chargerId": self._NEW_CHARGER_ID}
            await charger._client.close()

    async def test_updates_internal_state_after_success(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={}, status=200)

            charger = _make_charger()
            await charger.assign_charger(self._NEW_CHARGER_ID)

            assert charger.assigned_charger_id() == self._NEW_CHARGER_ID
            await charger._client.close()

    async def test_no_op_when_charger_id_unchanged(self) -> None:
        # Fixture already has chargerId = FAKE_CHARGER_ID; no HTTP call expected.
        charger = _make_charger()
        await charger.assign_charger(FAKE_CHARGER_ID)
        await charger._client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.patch(_BASE_URL, payload={"error": "bad request"}, status=400)

            charger = _make_charger()
            with pytest.raises(RequestError, match="Failed to assign charger"):
                await charger.assign_charger(self._NEW_CHARGER_ID)
            await charger._client.close()
