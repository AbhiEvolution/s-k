"""Pure time logic: no database, no HTTP."""
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.exceptions import InvalidRequestError
from app.services import slots

UTC = timezone.utc


def window(weekday, start, end):
    return SimpleNamespace(weekday=weekday, start_time=time(*start), end_time=time(*end))


MONDAY = date(2030, 1, 7)  # a Monday
assert MONDAY.weekday() == 0


def test_generate_slots_fills_the_window_in_order():
    result = slots.generate_slots(MONDAY, [window(0, (9, 0), (10, 30))])
    assert [s.strftime("%H:%M") for s in result] == ["09:00", "09:30", "10:00"]


def test_generate_slots_ignores_other_weekdays():
    assert slots.generate_slots(MONDAY, [window(1, (9, 0), (12, 0))]) == []


def test_generate_slots_handles_two_windows_a_day():
    result = slots.generate_slots(MONDAY, [window(0, (14, 0), (15, 0)), window(0, (9, 0), (10, 0))])
    assert [s.strftime("%H:%M") for s in result] == ["09:00", "09:30", "14:00", "14:30"]


def test_a_partial_slot_at_the_end_is_not_offered():
    result = slots.generate_slots(MONDAY, [window(0, (9, 0), (9, 45))])
    assert [s.strftime("%H:%M") for s in result] == ["09:00"]


def test_normalize_accepts_grid_times_and_converts_to_utc():
    plus_two = timezone(timedelta(hours=2))
    start = slots.normalize_start(datetime(2030, 1, 7, 11, 30, tzinfo=plus_two))
    assert start == datetime(2030, 1, 7, 9, 30, tzinfo=UTC) and start.utcoffset() == timedelta(0)


@pytest.mark.parametrize("minute, second", [(15, 0), (45, 0), (0, 30)])
def test_normalize_rejects_off_grid_times(minute, second):
    with pytest.raises(InvalidRequestError):
        slots.normalize_start(datetime(2030, 1, 7, 9, minute, second, tzinfo=UTC))


def test_fits_in_a_window():
    windows = [window(0, (9, 0), (10, 0))]
    assert slots.fits_in_a_window(datetime(2030, 1, 7, 9, 0, tzinfo=UTC), windows)
    assert slots.fits_in_a_window(datetime(2030, 1, 7, 9, 30, tzinfo=UTC), windows)
    assert not slots.fits_in_a_window(datetime(2030, 1, 7, 10, 0, tzinfo=UTC), windows)  # ends after
    assert not slots.fits_in_a_window(datetime(2030, 1, 7, 8, 30, tzinfo=UTC), windows)  # starts before
    assert not slots.fits_in_a_window(datetime(2030, 1, 8, 9, 0, tzinfo=UTC), windows)   # Tuesday


def test_slot_cannot_cross_midnight():
    windows = [window(0, (0, 0), (23, 30))]
    assert not slots.fits_in_a_window(datetime(2030, 1, 7, 23, 30, tzinfo=UTC), windows)
