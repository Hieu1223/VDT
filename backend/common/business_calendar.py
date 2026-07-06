"""Business calendar: configurable business days/hours + holiday list, used
to compute SLA due dates in business time rather than naive wall-clock time.
"""
from datetime import date, datetime, time, timedelta, timezone

from persistence.db import db

CONFIG_ID = "config"

DEFAULT_CALENDAR = {
    "id": CONFIG_ID,
    "_id": CONFIG_ID,
    "business_days": [0, 1, 2, 3, 4],  # Mon=0 ... Sun=6
    "start_hour": 9,
    "start_minute": 0,
    "end_hour": 17,
    "end_minute": 0,
    "holidays": [],  # list of "YYYY-MM-DD" strings
}


async def get_business_calendar() -> dict:
    config = await db.business_calendar.find_one({"id": CONFIG_ID})
    if not config:
        await db.business_calendar.insert_one(dict(DEFAULT_CALENDAR))
        return dict(DEFAULT_CALENDAR)
    config.pop("_id", None)
    return config


async def update_business_calendar(payload: dict) -> dict:
    await get_business_calendar()
    await db.business_calendar.update_one({"id": CONFIG_ID}, {"$set": payload})
    return await get_business_calendar()


def _is_business_day(moment: datetime, calendar: dict) -> bool:
    if moment.weekday() not in calendar["business_days"]:
        return False
    if moment.date().isoformat() in calendar.get("holidays", []):
        return False
    return True


def _day_start(moment: datetime, calendar: dict) -> datetime:
    return moment.replace(hour=calendar["start_hour"], minute=calendar["start_minute"], second=0, microsecond=0)


def _day_end(moment: datetime, calendar: dict) -> datetime:
    return moment.replace(hour=calendar["end_hour"], minute=calendar["end_minute"], second=0, microsecond=0)


def _next_business_day_start(moment: datetime, calendar: dict) -> datetime:
    candidate_date = moment.date() + timedelta(days=1)
    for _ in range(370):  # safety bound: at most ~a year out
        candidate_dt = datetime.combine(
            candidate_date, time(calendar["start_hour"], calendar["start_minute"]), tzinfo=moment.tzinfo
        )
        if _is_business_day(candidate_dt, calendar):
            return candidate_dt
        candidate_date += timedelta(days=1)
    return candidate_dt


def _snap_into_business_window(moment: datetime, calendar: dict) -> datetime:
    if _is_business_day(moment, calendar):
        start, end = _day_start(moment, calendar), _day_end(moment, calendar)
        if moment < start:
            return start
        if moment >= end:
            return _next_business_day_start(moment, calendar)
        return moment
    return _next_business_day_start(moment, calendar)


def add_business_minutes(start: datetime, minutes: int, calendar: dict) -> datetime:
    """Adds `minutes` of business time (skipping weekends/holidays/off-hours)
    to `start`, returning the resulting due datetime."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    current = _snap_into_business_window(start, calendar)
    remaining = minutes

    for _ in range(100000):  # safety bound against pathological configs
        if remaining <= 0:
            return current
        day_end = _day_end(current, calendar)
        available_today = (day_end - current).total_seconds() / 60
        if available_today <= 0:
            current = _next_business_day_start(current, calendar)
            continue
        if remaining <= available_today:
            return current + timedelta(minutes=remaining)
        remaining -= available_today
        current = _next_business_day_start(day_end, calendar)
    return current
