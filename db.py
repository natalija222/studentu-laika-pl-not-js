import sqlite3
from datetime import datetime


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(path):
    with connect(path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS events (
            uid TEXT PRIMARY KEY, title TEXT NOT NULL,
            starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
            imported_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_events_start ON events(starts_at)')


def replace_events(path, events):
    with connect(path) as db:
        db.execute('DELETE FROM events')
        now = datetime.now().astimezone().isoformat()
        db.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?)', [
            (e['uid'], e['title'], e['start'].isoformat(), e['end'].isoformat(), now)
            for e in events
        ])


def read_events(path):
    with connect(path) as db:
        rows = db.execute('SELECT uid, title, starts_at, ends_at FROM events ORDER BY starts_at').fetchall()
    return [{'uid': r['uid'], 'title': r['title'],
             'start': datetime.fromisoformat(r['starts_at']),
             'end': datetime.fromisoformat(r['ends_at'])} for r in rows]
