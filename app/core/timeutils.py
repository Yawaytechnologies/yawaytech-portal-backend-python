from datetime import datetime, date
from zoneinfo import ZoneInfo

from app.core.config import settings

IST = ZoneInfo(settings.TZ_NAME)
UTC = ZoneInfo("UTC")


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def to_local_date_ist(dt_utc: datetime) -> date:
    return dt_utc.astimezone(IST).date()
