"""Pure-function tests for frost-asset helpers (hours-since-sunset)."""

from __future__ import annotations

from datetime import UTC, datetime

from vindata_ingest.assets.frost_score import _hours_since_sunset


def test_hours_since_sunset_local_evening_just_after_18() -> None:
    # 19:00 local (Australia/Sydney UTC+10, fixed at Stage 00) ⇒ 1 hour past sunset.
    valid_utc = datetime(2026, 5, 7, 9, 0, tzinfo=UTC)  # 19:00 local
    assert _hours_since_sunset(valid_utc) == 1.0


def test_hours_since_sunset_local_morning_uses_previous_day_sunset() -> None:
    # 06:00 local ⇒ 12 hours past previous-day 18:00 sunset.
    valid_utc = datetime(2026, 5, 7, 20, 0, tzinfo=UTC)  # 06:00 local next day
    assert _hours_since_sunset(valid_utc) == 12.0


def test_hours_since_sunset_never_negative() -> None:
    # Tested across the full 24h cycle.
    base = datetime(2026, 5, 7, 0, 0, tzinfo=UTC)
    for h in range(24):
        valid = base.replace(hour=h)
        assert _hours_since_sunset(valid) >= 0
