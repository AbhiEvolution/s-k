"""Pure time logic: no database, no HTTP. Easy to test and to reason about.

All times are UTC. (A clinic time zone is a later improvement: it would live
in the clinic service's settings.)
"""
from datetime import date, datetime, time, timedelta, timezone

from app.core.config import get_settings
from app.core.exceptions import InvalidRequestError


def slot_length() -> timedelta:
    return timedelta(minutes=get_settings().slot_minutes)


def as_utc(value: datetime) -> datetime:
    """Treat naive datetimes (SQLite) as UTC; convert aware ones to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def on_grid(value: time | datetime) -> bool:
    """True for 09:00, 09:30, ... with no seconds."""
    if value.second or value.microsecond:
        return False
    return (value.hour * 60 + value.minute) % get_settings().slot_minutes == 0


def normalize_start(starts_at: datetime) -> datetime:
    """Validate a requested start time and return it in UTC."""
    start = as_utc(starts_at)
    if not on_grid(start):
        raise InvalidRequestError(
            f"Appointments start on a {get_settings().slot_minutes}-minute grid (for example 09:00 or 09:30 UTC)"
        )
    return start


def fits_in_a_window(start: datetime, windows) -> bool:
    """Does [start, start + slot) lie fully inside one of the doctor's windows that day?"""
    end = start + slot_length()
    if end.date() != start.date():  # a slot may not cross midnight
        return False
    return any(
        window.weekday == start.weekday()
        and window.start_time <= start.time()
        and end.time() <= window.end_time
        for window in windows
    )


def generate_slots(day: date, windows) -> list[datetime]:
    """All slot start times a doctor offers on `day`, in order."""
    length = slot_length()
    starts: list[datetime] = []
    for window in sorted(windows, key=lambda w: w.start_time):
        if window.weekday != day.weekday():
            continue
        current = datetime.combine(day, window.start_time, tzinfo=timezone.utc)
        limit = datetime.combine(day, window.end_time, tzinfo=timezone.utc)
        while current + length <= limit:
            starts.append(current)
            current += length
    return starts
