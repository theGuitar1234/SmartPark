from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil


@dataclass(frozen=True)
class TariffSnapshot:
    hourly_rate: float
    grace_minutes: int
    daily_max: float


def parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def calculate_fee(entry_time: str, exit_time: str, tariff: TariffSnapshot) -> float:
    entry = parse_time(entry_time)
    exit_at = parse_time(exit_time)
    if exit_at <= entry:
        raise ValueError("Exit time must be after entry time.")
    total_minutes = ceil((exit_at - entry).total_seconds() / 60)
    if total_minutes <= tariff.grace_minutes:
        return 0.0
    billable_minutes = total_minutes - tariff.grace_minutes
    full_days = billable_minutes // 1440
    remainder_minutes = billable_minutes % 1440
    amount = full_days * tariff.daily_max
    if remainder_minutes:
        hourly_amount = ceil(remainder_minutes / 60) * tariff.hourly_rate
        amount += min(hourly_amount, tariff.daily_max)
    return round(amount, 2)
