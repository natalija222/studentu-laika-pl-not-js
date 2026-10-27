"""Datu glabāšana un brīvā laika aprēķins. Tikai Python standarta bibliotēka."""
import sqlite3
from datetime import datetime, date, time, timedelta
from pathlib import Path


def stamp(value):
    return datetime.fromisoformat(value)


def free_slots(events, day, start='08:00', end='22:00', minimum=60):
    """Atņem apvienotos aizņemtos intervālus no izvēlētās dienas robežām."""
    left = datetime.combine(day, time.fromisoformat(start))
    right = datetime.combine(day, time.fromisoformat(end))
    if left >= right or not 1 <= minimum <= 1440:
        raise ValueError('Norādi derīgu dienas sākumu, beigas un ilgumu (1–1440 min).')
    busy = sorted((max(left, stamp(e['start'])), min(right, stamp(e['end'])))
                  for e in events if stamp(e['start']) < right and stamp(e['end']) > left)
    cursor, result = left, []
    for a, b in busy:
        if (a - cursor).total_seconds() >= minimum * 60:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if (right - cursor).total_seconds() >= minimum * 60:
        result.append((cursor, right))
    return result


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(__file__).resolve().parent / 'data' / 'planner.db'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY, title TEXT NOT NULL, minutes INTEGER NOT NULL,
              deadline TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY, title TEXT NOT NULL, start TEXT NOT NULL,
              end TEXT NOT NULL, kind TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'Manuāli',
              task_id INTEGER UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
              UNIQUE(title,start,end,source));
            ''')

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def events(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM events ORDER BY start')]

    def tasks(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT t.*, e.start AS planned
                FROM tasks t LEFT JOIN events e ON e.task_id=t.id ORDER BY t.deadline,t.id''')]

    def add_event(self, title, start, end, kind='Cits', source='Manuāli'):
        title = title.strip()
        a, b = stamp(start), stamp(end)
        if not title or len(title) > 150:
            raise ValueError('Nosaukumam jābūt 1–150 rakstzīmes garam.')
        if a.tzinfo or b.tzinfo or b <= a:
            raise ValueError('Beigu laikam jābūt pēc sākuma; izmanto vietējo laiku.')
        with self.connect() as db:
            db.execute('INSERT INTO events(title,start,end,kind,source) VALUES (?,?,?,?,?)',
                       (title,a.isoformat(timespec='minutes'),b.isoformat(timespec='minutes'),kind,source))

    def delete_event(self, event_id):
        with self.connect() as db:
            db.execute('DELETE FROM events WHERE id=?', (event_id,))

    def add_task(self, title, minutes, deadline):
        title = title.strip()
        due = date.fromisoformat(deadline)
        minutes = int(minutes)
        if not title or len(title) > 150 or not 1 <= minutes <= 840:
            raise ValueError('Norādi nosaukumu (1–150 rakstzīmes) un ilgumu (1–840 min).')
        with self.connect() as db:
            db.execute('INSERT INTO tasks(title,minutes,deadline) VALUES (?,?,?)', (title,minutes,due.isoformat()))

    def toggle_task(self, task_id):
        with self.connect() as db:
            db.execute('UPDATE tasks SET done=1-done WHERE id=?', (task_id,))

    def delete_task(self, task_id):
        with self.connect() as db:
            db.execute('DELETE FROM tasks WHERE id=?', (task_id,))

    def schedule(self, task_id, start, day_start='08:00', day_end='22:00'):
        a = stamp(start)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            task = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if not task or task['done']:
                raise ValueError('Izvēlies nepabeigtu uzdevumu.')
            if db.execute('SELECT id FROM events WHERE task_id=?', (task_id,)).fetchone():
                raise ValueError('Uzdevums jau ieplānots. Vispirms dzēs tā notikumu kalendārā.')
            b = a + timedelta(minutes=task['minutes'])
            if a < datetime.now() or b > datetime.combine(date.fromisoformat(task['deadline']), time.max):
                raise ValueError('Laikam jābūt nākotnē un ne vēlāk par uzdevuma termiņu.')
            events = [dict(r) for r in db.execute('SELECT * FROM events')]
            slots = free_slots(events, a.date(), day_start, day_end, task['minutes'])
            if not any(x <= a and b <= y for x, y in slots):
                raise ValueError('Šajā intervālā nepietiek brīva laika. Aprēķini laikus vēlreiz.')
            db.execute('INSERT INTO events(title,start,end,kind,source,task_id) VALUES (?,?,?,?,?,?)',
                       (task['title'],a.isoformat(timespec='minutes'),b.isoformat(timespec='minutes'),
                        'Mācības','Plānotājs',task_id))

    def seed(self, day):
        """Ielādē piemērus izvēlētajai nedēļai, nedublējot atkārtotu ielādi."""
        monday = day - timedelta(days=day.weekday())
        data = [(0,'09:00','10:30','Programmēšanas lekcija','Lekcija'),
                (0,'12:00','13:30','Datubāzu praktiskais darbs','Lekcija'),
                (1,'10:00','12:00','Datoru tīkli','Lekcija'),
                (1,'16:00','20:00','Darba maiņa','Darbs'),
                (2,'08:30','10:00','Matemātika','Lekcija'),
                (2,'13:00','15:00','Grupas projekta tikšanās','Cits'),
                (3,'09:00','11:30','Programmatūras izstrāde','Lekcija'),
                (4,'10:00','12:00','Laboratorijas darbs','Lekcija'),
                (5,'11:00','12:00','Sports','Atpūta')]
        count = 0
        for offset, a, b, title, kind in data:
            d = (monday + timedelta(days=offset)).isoformat()
            try:
                self.add_event(title, f'{d}T{a}', f'{d}T{b}', kind, 'Demo')
                count += 1
            except sqlite3.IntegrityError:
                pass
        return count

    def backup(self, destination):
        if Path(destination).resolve() == self.path.resolve():
            raise ValueError('Izvēlies citu failu, nevis aktīvo datubāzi.')
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)

    def replace_google(self, events):
        """Atomic snapshot replacement; manual/demo/task events are preserved."""
        rows=[]
        for e in events:
            a,b=stamp(e['start']),stamp(e['end'])
            if a.tzinfo or b.tzinfo or a>=b or not e['title'].strip():
                raise ValueError('Nederīgi Google dati; iepriekšējie dati saglabāti.')
            rows.append((e['title'],a.isoformat(),b.isoformat(),'Google','Google Calendar'))
        with self.connect() as db:
            db.execute("DELETE FROM events WHERE source='Google Calendar'")
            db.executemany('INSERT OR IGNORE INTO events(title,start,end,kind,source) VALUES (?,?,?,?,?)',rows)
