from typing import Optional
import pytz
from datetime import datetime, timezone

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
UTC_TZ = pytz.UTC


def convert_to_moscow_time(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
        
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
        
    moscow_time = dt.astimezone(MOSCOW_TZ)
    return moscow_time.replace(tzinfo=None)


def parse_iso_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    if not iso_string:
        return None

    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return convert_to_moscow_time(dt)


def make_timezone_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
        
    # First convert to Moscow
    moscow_dt = dt.astimezone(MOSCOW_TZ)
    # Then remove timezone info
    return moscow_dt.replace(tzinfo=None)


def make_timezone_aware(dt: datetime, tz=timezone.utc) -> datetime:
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=tz)
