"""Notification models (``/api/v1/users/{uid}/notifications/*``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Notification:
    """A single push/in-app notification delivered to a user.

    Returned as part of :class:`NotificationsList` by
    :meth:`~onekommafive.System.get_notifications`.
    """

    id: str
    """Notification UUID."""

    type: str
    """Notification category (e.g. ``"ENERGY_MARKET_UPPER_TARGET_REACHED"``, ``"SYSTEM_HEALTH"``)."""

    title: str | None
    """Localised title of the notification."""

    body: str | None
    """Localised body text."""

    locale: str | None
    """Locale used for the title/body, e.g. ``"de"``."""

    system_id: str | None
    """UUID of the system the notification relates to."""

    user_id: str | None
    """UUID of the recipient user."""

    created_at: str | None
    """ISO-8601 timestamp when the notification was created."""

    read: bool | None
    """Whether the user has opened the notification."""

    dismissed: bool | None
    """Whether the user has dismissed the notification."""

    meta: dict[str, Any]
    """Free-form meta data attached by the API (e.g. ``{"price": {...}, "dateTime_utc": ...}``)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        details = data.get("notificationDetails") or {}
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            title=data.get("title"),
            body=data.get("body"),
            locale=data.get("locale"),
            system_id=data.get("systemId"),
            user_id=data.get("userId"),
            created_at=data.get("createdAt"),
            read=data.get("read"),
            dismissed=data.get("dismissed"),
            meta=details.get("meta") or {},
            raw=data,
        )


@dataclass
class NotificationsList:
    """Recent notifications for a user, scoped to one system.

    Returned by :meth:`~onekommafive.System.get_notifications`
    (``GET /api/v1/users/{uid}/notifications/latest?systemId={id}``).
    """

    notifications: list[Notification]
    """Notifications in the response (typically newest-first)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationsList":
        return cls(
            notifications=[Notification.from_dict(n) for n in data.get("data") or []],
            raw=data,
        )


@dataclass
class NotificationChannelSettings:
    """Per-subscription channel toggles for one notification category."""

    subscription_id: str | None
    """Underlying subscription UUID."""

    app: bool | None
    """In-app notifications enabled."""

    push: bool | None
    """Push notifications enabled."""

    email: bool | None
    """Email notifications enabled."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationChannelSettings":
        ch = data.get("channels") or {}
        return cls(
            subscription_id=data.get("subscriptionId"),
            app=ch.get("app"),
            push=ch.get("push"),
            email=ch.get("email"),
            raw=data,
        )


@dataclass
class NotificationSettings:
    """User's notification preferences per category for one system.

    Returned by :meth:`~onekommafive.System.get_notification_settings`
    (``GET /api/v1/systems/{id}/users/{uid}/notifications/settings``).
    """

    lang_code: str | None
    """Preferred language for notifications, e.g. ``"de"``."""

    settings: dict[str, list[NotificationChannelSettings]]
    """Per-category subscriptions. Keys are notification types
    (``"CO2_IMPACT"``, ``"BATTERY_SOC"``, ``"BROADCAST_NEW_ELECTRICITY_PRICES"``,
    ``"SYSTEM_HEALTH"``, ``"ENERGY_MARKET_UPPER_TARGET_REACHED"``,
    ``"ENERGY_MARKET_LOWER_TARGET_REACHED"``, ``"EV_DYNAMIC_PULSE"``,
    ``"SYSTEM_DATA_COLLECTION_ENDED"``). Value is a list of channel-toggle
    entries (empty when the user has not subscribed to that category)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationSettings":
        raw_settings = data.get("settings") or {}
        parsed = {
            category: [NotificationChannelSettings.from_dict(e) for e in entries or []]
            for category, entries in raw_settings.items()
        }
        return cls(
            lang_code=data.get("langCode"),
            settings=parsed,
            raw=data,
        )
