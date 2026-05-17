"""Weather forecast models (``/api/v1/systems/{id}/weather``)."""

from dataclasses import dataclass, field
from typing import Any

WEATHER_SYMBOLS: dict[int, str] = {
    1: "Sonnig / klar",
    2: "Heiter",
    3: "Wechselnd bewölkt",
    4: "Bedeckt",
    5: "Regen",
    8: "Leicht bewölkt mit Schauern",
    15: "Starker Regen",
    # Night variants (day ID + 100)
    101: "Klar (Nacht)",
    102: "Heiter (Nacht)",
    103: "Wechselnd bewölkt (Nacht)",
    104: "Bedeckt (Nacht)",
    105: "Regen (Nacht)",
    108: "Schauer (Nacht)",
    115: "Starker Regen (Nacht)",
}
"""Map from ``weatherSymbolId`` to a human-readable description."""


@dataclass
class WeatherDay:
    """Daily weather summary for today or tomorrow.

    Part of :class:`WeatherData` returned by :meth:`~onekommafive.System.get_weather`.
    """

    temperature_celsius: float | None
    """Daytime high temperature, in °C."""

    precipitation_mm: float | None
    """Total precipitation, in mm."""

    precipitation_probability: float | None
    """Precipitation probability as a percentage (0–100)."""

    sunshine_minutes: float | None
    """Forecast sunshine duration, in minutes."""

    sunrise: str | None
    """ISO-8601 sunrise timestamp (UTC)."""

    sunset: str | None
    """ISO-8601 sunset timestamp (UTC)."""

    weather_symbol_id: int | None
    """Weather symbol code; see :data:`WEATHER_SYMBOLS` for descriptions."""

    @property
    def weather_description(self) -> str:
        """Human-readable weather description derived from :attr:`weather_symbol_id`."""
        if self.weather_symbol_id is None:
            return "—"
        return WEATHER_SYMBOLS.get(self.weather_symbol_id, f"Symbol {self.weather_symbol_id}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeatherDay":
        """Construct a :class:`WeatherDay` from a raw API dict."""
        return cls(
            temperature_celsius=data.get("temperatureCelsius"),
            precipitation_mm=data.get("precipitationMm"),
            precipitation_probability=data.get("precipitationProbability"),
            sunshine_minutes=data.get("sunshineMinutes"),
            sunrise=data.get("sunrise"),
            sunset=data.get("sunset"),
            weather_symbol_id=data.get("weatherSymbolId"),
        )


@dataclass
class WeatherSlot:
    """A 3-hour forecast slot in the fine-grained weather forecast.

    Part of :class:`WeatherData` returned by :meth:`~onekommafive.System.get_weather`.
    """

    period_start: str
    """ISO-8601 start of the 3-hour slot (UTC)."""

    temperature_celsius: float | None
    """Temperature at the start of the slot, in °C."""

    wind_speed: float | None
    """Wind speed, in m/s."""

    precipitation_mm: float | None
    """Precipitation in the slot, in mm."""

    precipitation_probability: float | None
    """Precipitation probability as a percentage (0–100)."""

    sunshine_minutes: float | None
    """Sunshine duration within the slot, in minutes (max ~180 for a 3h slot)."""

    weather_symbol_id: int | None
    """Weather symbol code; see :data:`WEATHER_SYMBOLS` for descriptions."""

    @property
    def weather_description(self) -> str:
        """Human-readable weather description derived from :attr:`weather_symbol_id`."""
        if self.weather_symbol_id is None:
            return "—"
        return WEATHER_SYMBOLS.get(self.weather_symbol_id, f"Symbol {self.weather_symbol_id}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeatherSlot":
        """Construct a :class:`WeatherSlot` from a raw API dict."""
        return cls(
            period_start=data["periodStart"],
            temperature_celsius=data.get("temperatureCelsius"),
            wind_speed=data.get("windSpeed"),
            precipitation_mm=data.get("precipitationMm"),
            precipitation_probability=data.get("precipitationProbability"),
            sunshine_minutes=data.get("sunshineMinutes"),
            weather_symbol_id=data.get("weatherSymbolId"),
        )


@dataclass
class WeatherData:
    """Weather forecast for a 1KOMMA5° system site.

    Returned by :meth:`~onekommafive.System.get_weather`.
    Includes daily summaries for today and tomorrow as well as 3-hour slots
    covering the next 48 hours.
    """

    today: WeatherDay
    """Daily summary for today."""

    tomorrow: WeatherDay
    """Daily summary for tomorrow."""

    forecasts: list[WeatherSlot]
    """3-hour forecast slots for the next 48 hours, ordered chronologically."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeatherData":
        """Construct a :class:`WeatherData` from a raw API response dict."""
        return cls(
            today=WeatherDay.from_dict(data.get("today", {})),
            tomorrow=WeatherDay.from_dict(data.get("tomorrow", {})),
            forecasts=[WeatherSlot.from_dict(s) for s in data.get("fineGrainedForecasts", [])],
            raw=data,
        )
