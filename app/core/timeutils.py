from datetime import datetime, date
from zoneinfo import ZoneInfo
import calendar

from app.core.config import settings

IST = ZoneInfo(settings.TZ_NAME)
UTC = ZoneInfo("UTC")


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def to_local_date_ist(dt_utc: datetime) -> date:
    return dt_utc.astimezone(IST).date()


def _to_hours_minutes(seconds: int) -> str:
    """Convert seconds to HH:MM format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def _last_day_of_month(year: int, month: int) -> int:
    """Get the last day of the month."""
    return calendar.monthrange(year, month)[1]


def _is_weekend(d: date) -> bool:
    """Check if the date is a weekend (Saturday or Sunday)."""
    return d.weekday() >= 5  # 5=Saturday, 6=Sunday


def _avg_hhmm(total_seconds: int, count: int) -> str:
    """Calculate average hours:minutes from total seconds and count."""
    if count == 0:
        return "00:00"
    avg_seconds = total_seconds // count
    return _to_hours_minutes(avg_seconds)
