import time
from datetime import datetime, date, timezone

def now_unix():
    """Текущее время в Unix timestamp"""
    return int(time.time())

def datetime_to_unix(dt):
    """Преобразует datetime в Unix timestamp"""
    if not dt:
        return None
    return int(dt.replace(tzinfo=timezone.utc).timestamp())

def unix_to_datetime(unix_time):
    """Преобразует Unix timestamp в datetime"""
    if not unix_time:
        return None
    return datetime.fromtimestamp(unix_time, tz=timezone.utc)

def date_to_unix(d):
    """Преобразует date в Unix timestamp (полночь)"""
    if not d:
        return None
    dt = datetime.combine(d, datetime.min.time(), timezone.utc)
    return int(dt.timestamp())

def unix_to_date(unix_time):
    """Преобразует Unix timestamp в date"""
    if not unix_time:
        return None
    dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    return dt.date()