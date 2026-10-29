"""Read an explicitly public Google Calendar iCalendar feed. No Google password/OAuth token."""
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests
from icalendar import Calendar
from dateutil.rrule import rrulestr

MAX_BYTES = 5_000_000


def validate_feed_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme != 'https' or parsed.hostname not in {'calendar.google.com', 'www.google.com'}:
        raise ValueError('Atļauta tikai publiska Google Calendar HTTPS iCalendar saite.')
    if not parsed.path.endswith('.ics'):
        raise ValueError('Google Calendar saitei jābeidzas ar .ics')
    return url.strip()


def _as_datetime(value, tz):
    if isinstance(value, datetime):
        return value.replace(tzinfo=tz) if value.tzinfo is None else value.astimezone(tz)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=tz)
    raise ValueError('Nederīgs kalendāra datums')


def fetch_events(url, start_day, end_day, tz_name='Europe/Riga'):
    """Return events overlapping inclusive day range. Supports simple RRULE and EXDATE."""
    url = validate_feed_url(url)
    tz = ZoneInfo(tz_name)
    response = requests.get(url, timeout=20, allow_redirects=False, headers={'User-Agent': 'StudentuLaikaPlanotajs/1.0'})
    response.raise_for_status()
    if len(response.content) > MAX_BYTES:
        raise ValueError('Kalendāra fails ir pārāk liels.')
    calendar = Calendar.from_ical(response.content)
    window_start = datetime.combine(start_day, time.min, tzinfo=tz)
    window_end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=tz)
    events = []
    for component in calendar.walk('VEVENT'):
        if component.get('RECURRENCE-ID') is not None:
            # Detached recurrence overrides need a full recurrence engine; skip rather than duplicate.
            continue
        raw_start = component.decoded('DTSTART')
        raw_end = component.decoded('DTEND') if component.get('DTEND') else raw_start + timedelta(hours=1)
        event_start, event_end = _as_datetime(raw_start, tz), _as_datetime(raw_end, tz)
        if event_end <= event_start:
            continue
        duration = event_end - event_start
        occurrences = [event_start]
        if component.get('RRULE'):
            rule = component.get('RRULE').to_ical().decode('utf-8')
            try:
                series = rrulestr(rule, dtstart=event_start)
                occurrences = list(series.between(window_start - duration, window_end, inc=True))[:2000]
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Neatbalstīts atkārtošanās noteikums: {exc}') from exc
        excluded = set()
        exdates = component.get('EXDATE', [])
        if not isinstance(exdates, list):
            exdates = [exdates]
        for item in exdates:
            for item_date in item.dts:
                excluded.add(_as_datetime(item_date.dt, tz))
        uid = str(component.get('UID', 'bez-id'))
        summary = str(component.get('SUMMARY', 'Bez nosaukuma'))
        for occurrence in occurrences:
            occurrence = _as_datetime(occurrence, tz)
            end = occurrence + duration
            if occurrence in excluded or end <= window_start or occurrence >= window_end:
                continue
            events.append({'uid': f'{uid}|{occurrence.isoformat()}', 'title': summary,
                           'start': occurrence, 'end': end})
    return events
