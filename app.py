
import os
from datetime import date, timedelta, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)

from core import free_intervals
from db import initialize, replace_events, read_events
from google_calendar import fetch_events


BASE = Path(__file__).resolve().parent
DB_PATH = os.getenv(
    'DATABASE_PATH',
    str(BASE / 'planner.sqlite3')
)

TZ = ZoneInfo('Europe/Riga')

app = Flask(__name__)
app.secret_key = os.getenv(
    'FLASK_SECRET_KEY',
    'local-demo-only-change-in-production'
)

initialize(DB_PATH)


def clamp_int(value, default, minimum, maximum):
    try:
        number = int(value)
        return number if minimum <= number <= maximum else default
    except (TypeError, ValueError):
        return default


def get_day_events(all_events, day):
    """Atlasa notikumus, kas pārklājas ar izvēlēto dienu."""
    day_start = datetime.combine(day, time.min, tzinfo=TZ)
    day_end = datetime.combine(
        day + timedelta(days=1),
        time.min,
        tzinfo=TZ
    )

    return [
        event for event in all_events
        if event['start'].astimezone(TZ) < day_end
        and event['end'].astimezone(TZ) > day_start
    ]


def prepare_day(all_events, day, start_hour, end_hour, minimum):
    """Sagatavo vienas dienas notikumus un brīvos intervālus."""
    day_events = get_day_events(all_events, day)

    free = free_intervals(
        day_events,
        day,
        start_hour,
        end_hour,
        minimum,
        TZ
    )

    busy_view = [
        {
            'title': event['title'],
            'start': event['start'].astimezone(TZ).strftime('%H:%M'),
            'end': event['end'].astimezone(TZ).strftime('%H:%M')
        }
        for event in day_events
    ]

    free_view = [
        {
            'start': start.strftime('%H:%M'),
            'end': end.strftime('%H:%M'),
            'minutes': round(
                (end - start).total_seconds() / 60
            )
        }
        for start, end in free
    ]

    return {
        'date': day.isoformat(),
        'events': busy_view,
        'free': free_view,
        'total_free': sum(
            item['minutes'] for item in free_view
        )
    }


@app.get('/')
def index():
    selected = request.args.get(
        'day',
        date.today().isoformat()
    )

    try:
        day = date.fromisoformat(selected)
    except ValueError:
        day = date.today()

    start_hour = clamp_int(
        request.args.get('from'), 8, 0, 23
    )
    end_hour = clamp_int(
        request.args.get('to'), 22,
        start_hour + 1, 24
    )
    minimum = clamp_int(
        request.args.get('min'), 30, 1, 1440
    )

    all_events = read_events(DB_PATH)

    result = prepare_day(
        all_events,
        day,
        start_hour,
        end_hour,
        minimum
    )

    return render_template(
        'index.html',
        day=result['date'],
        start_hour=start_hour,
        end_hour=end_hour,
        minimum=minimum,
        events=result['events'],
        free=result['free'],
        total=len(all_events),
        total_free=result['total_free'],
        configured=bool(
            os.getenv('GOOGLE_CALENDAR_ICS_URL')
        )
    )


@app.get('/two-weeks')
def two_weeks():
    """Aprēķina brīvos laikus nākamajām 14 dienām."""
    start_day = date.today()

    start_hour = clamp_int(
        request.args.get('from'), 8, 0, 23
    )
    end_hour = clamp_int(
        request.args.get('to'), 22,
        start_hour + 1, 24
    )
    minimum = clamp_int(
        request.args.get('min'), 30, 1, 1440
    )

    all_events = read_events(DB_PATH)

    days = []

    for offset in range(14):
        current_day = start_day + timedelta(days=offset)

        result = prepare_day(
            all_events,
            current_day,
            start_hour,
            end_hour,
            minimum
        )

        days.append(result)

    return render_template(
        'two_weeks.html',
        days=days,
        start_hour=start_hour,
        end_hour=end_hour,
        minimum=minimum
    )


@app.post('/sync')
def sync():
    url = os.getenv(
        'GOOGLE_CALENDAR_ICS_URL', ''
    ).strip()

    if not url:
        flash(
            'Nav iestatīts GOOGLE_CALENDAR_ICS_URL.',
            'error'
        )
        return redirect(url_for('index'))

    try:
        today = date.today()

        events = fetch_events(
            url,
            today - timedelta(days=90),
            today + timedelta(days=365)
        )

        replace_events(DB_PATH, events)

        flash(
            f'Kalendārs sinhronizēts! '
            f'Datubāzē saglabāti {len(events)} notikumi.',
            'success'
        )

    except Exception as exc:
        flash(
            f'Sinhronizācija neizdevās: {exc}',
            'error'
        )

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', '8000')),
        debug=False
    )
