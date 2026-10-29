from datetime import datetime, timedelta


def free_intervals(events, day, start_hour=8, end_hour=22, min_minutes=30, tz=None):
    """Return free (start, end) aware datetimes, merging overlapping busy events."""
    if not (0 <= start_hour < end_hour <= 24):
        raise ValueError('Nederīgs dienas sākuma vai beigu laiks.')
    if not (1 <= min_minutes <= 1440):
        raise ValueError('Nederīgs minimālais intervāls.')
    start = datetime.combine(day, datetime.min.time(), tzinfo=tz) + timedelta(hours=start_hour)
    end = datetime.combine(day, datetime.min.time(), tzinfo=tz) + timedelta(hours=end_hour)
    busy = []
    for event in events:
        a, b = event['start'], event['end']
        if a.tzinfo is None or b.tzinfo is None:
            raise ValueError('Notikumu laikam jābūt ar laika joslu.')
        a, b = a.astimezone(tz), b.astimezone(tz)
        a, b = max(a, start), min(b, end)
        if a < b:
            busy.append((a, b))
    busy.sort(key=lambda item: item[0])
    merged = []
    for a, b in busy:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    free, cursor = [], start
    for a, b in merged:
        if (a - cursor).total_seconds() >= min_minutes * 60:
            free.append((cursor, a))
        cursor = max(cursor, b)
    if (end - cursor).total_seconds() >= min_minutes * 60:
        free.append((cursor, end))
    return free
