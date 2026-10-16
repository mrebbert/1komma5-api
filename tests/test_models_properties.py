"""Property-based tests for ``from_dict`` constructors.

The FAQ promises that model dataclasses stay graceful when the backend
drops previously-populated optional keys. These tests prove it: for a
curated set of representative models, hypothesis builds random subsets
of a known-good reference payload and checks that

- construction never raises on a subset that keeps the mandatory keys;
- ``.raw`` round-trips the input the model saw.

Covering every model is intentionally out of scope here: the generic
``_dict_subset_keeping`` strategy only drops top-level keys, so nested
mandatory-key paths need per-model work. The representatives below
exercise the most frequently-shaped shapes (flat dict, nested dict,
list-of-dicts).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from onekommafive.models import (
    Customer,
    EmsSettings,
    EnergyData,
    HeartbeatAiSummary,
    HeartbeatPrices,
    ImpactOverview,
    LiveOverview,
    MarketPrices,
    Notification,
    NotificationSettings,
    NotificationsList,
    SiteDetails,
    SiteStatus,
    SiteSystemInfo,
    SmartMeter,
    SupportedVersions,
    SystemDetails,
    SystemInfo,
    User,
    WeatherData,
)
from tests.fixtures import (
    make_customer_data,
    make_ems_settings_data,
    make_energy_data,
    make_heartbeat_ai_summary_data,
    make_heartbeat_prices_data,
    make_impact_overview_data,
    make_live_overview_data,
    make_notification_settings_data,
    make_notifications_data,
    make_price_data,
    make_site_details_data,
    make_smart_meter_data,
    make_status_and_assets_data,
    make_supported_versions_data,
    make_system_data,
    make_system_details_data,
    make_system_info_data,
    make_user_data,
    make_weather_data,
)


@st.composite
def _dict_subset_keeping(
    draw: st.DrawFn, source: dict[str, Any], keep: tuple[str, ...]
) -> dict[str, Any]:
    """Draw a random subset of ``source`` that always retains ``keep``."""

    droppable = tuple(sorted(set(source) - set(keep)))
    if not droppable:
        return dict(source)
    dropped = draw(st.sets(st.sampled_from(droppable)))
    return {k: v for k, v in source.items() if k not in dropped}


def _call_hbai(data: dict[str, Any]) -> HeartbeatAiSummary:
    """``HeartbeatAiSummary.from_dict`` takes an extra ``resolution`` argument."""

    return HeartbeatAiSummary.from_dict("1M", data)


MODEL_CASES: list[
    tuple[
        str,
        Callable[[dict[str, Any]], Any],
        Callable[[], dict[str, Any]],
        tuple[str, ...],
    ]
] = [
    # (label, from_dict_callable, make_reference_data, mandatory_top_level_keys)
    ("SystemInfo", SystemInfo.from_dict, make_system_data, ("id",)),
    ("SystemDetails", SystemDetails.from_dict, make_system_details_data, ("id",)),
    ("SiteDetails", SiteDetails.from_dict, make_site_details_data, ("id",)),
    ("SiteStatus", SiteStatus.from_dict, make_status_and_assets_data, ()),
    (
        "SiteSystemInfo-enrolled",
        SiteSystemInfo.from_dict,
        lambda: make_system_info_data(
            availability="READY",
            enwg14a_module_value="module-1",
            enwg14a_module_valid_from="2025-09-19",
        ),
        (),
    ),
    (
        "SiteSystemInfo-blank",
        SiteSystemInfo.from_dict,
        make_system_info_data,
        (),
    ),
    ("LiveOverview", LiveOverview.from_dict, make_live_overview_data, ()),
    (
        "MarketPrices",
        MarketPrices.from_dict,
        make_price_data,
        (
            "energyMarket",
            "timeseries",
            "gridCostsTotal",
            "usesFallbackGridCosts",
            "vat",
        ),
    ),
    ("EnergyData", EnergyData.from_dict, make_energy_data, ()),
    ("HeartbeatPrices", HeartbeatPrices.from_dict, make_heartbeat_prices_data, ()),
    ("HeartbeatAiSummary", _call_hbai, make_heartbeat_ai_summary_data, ()),
    ("ImpactOverview", ImpactOverview.from_dict, make_impact_overview_data, ()),
    ("Customer", Customer.from_dict, make_customer_data, ("id",)),
    ("User", User.from_dict, make_user_data, ("id", "email")),
    ("SmartMeter", SmartMeter.from_dict, make_smart_meter_data, ()),
    ("WeatherData", WeatherData.from_dict, make_weather_data, ()),
    (
        "NotificationsList",
        NotificationsList.from_dict,
        make_notifications_data,
        (),
    ),
    (
        "Notification",
        Notification.from_dict,
        lambda: make_notifications_data()["data"][0],
        ("id",),
    ),
    (
        "NotificationSettings",
        NotificationSettings.from_dict,
        make_notification_settings_data,
        (),
    ),
    (
        "SupportedVersions",
        SupportedVersions.from_dict,
        make_supported_versions_data,
        (),
    ),
    ("EmsSettings", EmsSettings.from_dict, make_ems_settings_data, ()),
]


@pytest.mark.parametrize(
    ("label", "from_dict", "make_data", "mandatory"),
    MODEL_CASES,
    ids=[case[0] for case in MODEL_CASES],
)
@settings(
    max_examples=40,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(data=st.data())
def test_from_dict_robust_to_missing_optional_keys(
    label: str,
    from_dict: Callable[[dict[str, Any]], Any],
    make_data: Callable[[], dict[str, Any]],
    mandatory: tuple[str, ...],
    data: st.DataObject,
) -> None:
    """Dropping any combination of non-mandatory keys from the reference
    payload must not break construction, and ``.raw`` must round-trip."""

    reference = make_data()
    subset = data.draw(_dict_subset_keeping(reference, mandatory))
    model = from_dict(subset)
    assert model.raw == subset


# ---------------------------------------------------------------------------
# Degenerate inputs: empty dict against models that document "all optional".
# ---------------------------------------------------------------------------


ALL_OPTIONAL_CASES: list[tuple[str, Callable[[dict[str, Any]], Any]]] = [
    ("SiteStatus", SiteStatus.from_dict),
    ("SiteSystemInfo", SiteSystemInfo.from_dict),
    ("LiveOverview", LiveOverview.from_dict),
    ("EnergyData", EnergyData.from_dict),
    ("HeartbeatPrices", HeartbeatPrices.from_dict),
    ("ImpactOverview", ImpactOverview.from_dict),
    ("SmartMeter", SmartMeter.from_dict),
    ("WeatherData", WeatherData.from_dict),
    ("NotificationsList", NotificationsList.from_dict),
    ("NotificationSettings", NotificationSettings.from_dict),
    ("SupportedVersions", SupportedVersions.from_dict),
    ("EmsSettings", EmsSettings.from_dict),
]


@pytest.mark.parametrize(
    ("label", "from_dict"),
    ALL_OPTIONAL_CASES,
    ids=[case[0] for case in ALL_OPTIONAL_CASES],
)
def test_from_dict_accepts_empty_payload(
    label: str, from_dict: Callable[[dict[str, Any]], Any]
) -> None:
    """Models whose top-level keys are all optional must construct from ``{}``."""

    model = from_dict({})
    assert model.raw == {}
