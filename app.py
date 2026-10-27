"""Studentu laika plānotājs: Flask + SQLite. Palaist ar python app.py."""
import csv
import io
import json
import os
import secrets
import sqlite3
import tempfile
import threading
import time as clock
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for
from werkzeug.exceptions import SecurityError
from core import Store, free_slots
import google_calendar as google

ROOT = Path(__file__).resolve().parent
DAYS = ['Pirmdiena', 'Otrdiena', 'Trešdiena', 'Ceturtdiena', 'Piektdiena', 'Sestdiena', 'Svētdiena']
TABS = [('calendar', 'Kalendārs'), ('free', 'Brīvais laiks'), ('tasks', 'Mācību uzdevumi'), ('connections', 'Savienojumi')]
KINDS = ['Lekcija', 'Darbs', 'Mācības', 'Atpūta', 'Cits']

# Linux / Codespaces uses Riga time just as the previous desktop environment did.
if hasattr(clock, 'tzset'):
    os.environ.setdefault('TZ', 'Europe/Riga')
    clock.tzset()


def public_url():
    if os.environ.get('PLANNER_PUBLIC_URL'):
        result = os.environ['PLANNER_PUBLIC_URL'].rstrip('/')
    elif os.environ.get('CODESPACE_NAME'):
        domain = os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
        result = f"https://{os.environ['CODESPACE_NAME']}-8000.{domain}"
    else:
        result = 'http://localhost:8000'
    parsed = urlsplit(result)
    if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.path
            or parsed.query or parsed.fragment or parsed.username
            or (parsed.scheme == 'http' and parsed.hostname not in {'localhost', '127.0.0.1'})):
        raise ValueError('PLANNER_PUBLIC_URL jābūt HTTPS sākumadresei vai http://localhost:8000.')
    return result


def create_app(db_path=None, credentials_path=None, base_url=None):
    app = Flask(__name__)
    base = base_url or public_url()
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=128 * 1024,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=base.startswith('https://'),
                      TRUSTED_HOSTS=['localhost', '127.0.0.1', urlsplit(base).hostname])
    store = Store(db_path)
    config_path = Path(credentials_path) if credentials_path else ROOT / 'credentials.json'
    sessions = {}
    lock = threading.RLock()
    app.extensions['store'] = store
    app.extensions['google_sessions'] = sessions
    callback = base + '/google/callback'

    def browser_state():
        sid = session['sid']
        with lock:
            state = sessions.setdefault(sid, {'credentials': None, 'pending': None, 'updated': None,
                                             'lock': threading.RLock()})
            state['seen'] = clock.monotonic()
            return state

    @app.before_request
    def protect():
        if 'sid' not in session:
            session['sid'] = secrets.token_urlsafe(32)
            session['csrf'] = secrets.token_urlsafe(32)
        if request.method == 'POST':
            sent = request.form.get('csrf', '')
            if not sent or not secrets.compare_digest(sent, session.get('csrf', '')):
                abort(400, description='Sesija mainījusies. Atjauno lapu un atkārto darbību.')
        with lock:
            for sid in list(sessions):
                if clock.monotonic() - sessions[sid].get('seen', 0) > 43200:
                    del sessions[sid]

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
        return response

    def settings():
        return dict(session.get('view', {'day': date.today().isoformat(), 'period': 'week',
                                        'start': '08:00', 'end': '22:00', 'minimum': 60}))

    def dates(view):
        day = date.fromisoformat(view['day'])
        if view['period'] == 'day':
            return [day]
        first = day - timedelta(days=day.weekday())
        return [first + timedelta(days=i) for i in range(7)]

    def visible_events(view):
        days = dates(view)
        left = datetime.combine(days[0], datetime.min.time())
        right = datetime.combine(days[-1] + timedelta(days=1), datetime.min.time())
        return [e for e in store.events() if datetime.fromisoformat(e['start']) < right
                and datetime.fromisoformat(e['end']) > left]

    def slots_for(view):
        result = []
        now = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        events = store.events()
        for day in dates(view):
            for start, end in free_slots(events, day, view['start'], view['end'], view['minimum']):
                start = max(start, now)
                if (end-start).total_seconds() >= view['minimum'] * 60:
                    result.append({'start': start, 'end': end, 'minutes': int((end-start).total_seconds()/60)})
        return result

    def back(tab=None):
        selected = tab or request.form.get('tab', 'calendar')
        if selected not in dict(TABS):
            selected = 'calendar'
        return redirect(url_for('index', tab=selected), code=303)

    @app.get('/')
    def index():
        view = settings()
        tab = request.args.get('tab', 'calendar')
        if tab not in dict(TABS):
            tab = 'calendar'
        events, tasks, slots = visible_events(view), store.tasks(), slots_for(view)
        state = browser_state()
        days = dates(view)
        return render_template('index.html', tab=tab, tabs=TABS, view=view, days=days, daynames=DAYS,
                               events=events, tasks=tasks, slots=slots, kinds=KINDS,
                               available=[t for t in tasks if not t['done'] and not t['planned']],
                               open_tasks=sum(not t['done'] for t in tasks),
                               free_minutes=sum(s['minutes'] for s in slots), today=date.today().isoformat(),
                               due=(date.today()+timedelta(days=7)).isoformat(),
                               connected=state['credentials'] is not None, updated=state['updated'],
                               configured=config_path.exists(), callback=callback, csrf=session['csrf'])

    @app.post('/view')
    def set_view():
        view = settings()
        view.update(day=request.form['day'], period=request.form['period'], start=request.form['start'],
                    end=request.form['end'], minimum=int(request.form['minimum']))
        if view['period'] not in {'day', 'week'}:
            raise ValueError('Izvēlies dienas vai nedēļas skatu.')
        # Validate all settings before replacing previous good values.
        selected_days = dates(view)
        free_slots([], selected_days[0], view['start'], view['end'], view['minimum'])
        session['view'] = view
        return back()

    @app.post('/events')
    def add_event():
        kind = request.form.get('kind', 'Cits')
        if kind not in KINDS:
            raise ValueError('Nederīgs notikuma veids.')
        store.add_event(request.form['title'], request.form['start'], request.form['end'], kind)
        flash('Notikums saglabāts datubāzē.', 'success')
        return back('calendar')

    @app.post('/events/<int:event_id>/delete')
    def delete_event(event_id):
        event = next((e for e in store.events() if e['id'] == event_id), None)
        if event is None:
            raise ValueError('Notikums vairs nav pieejams.')
        if event['source'] == 'Google Calendar':
            raise ValueError('Google notikumu maini Google Calendar un pēc tam ielādē atkārtoti.')
        store.delete_event(event_id)
        flash('Notikums dzēsts. Brīvais laiks pārrēķināts.', 'success')
        return back('calendar')

    @app.post('/demo')
    def demo():
        count = store.seed(date.fromisoformat(settings()['day']))
        flash(f'Ielādēti {count} demo notikumi. Tie nav iegūti no Google.', 'success')
        return back('calendar')

    @app.post('/tasks')
    def add_task():
        store.add_task(request.form['title'], request.form['minutes'], request.form['deadline'])
        flash('Mācību uzdevums saglabāts.', 'success')
        return back('tasks')

    @app.post('/tasks/<int:task_id>/toggle')
    def toggle_task(task_id):
        store.toggle_task(task_id)
        return back('tasks')

    @app.post('/tasks/<int:task_id>/delete')
    def delete_task(task_id):
        store.delete_task(task_id)
        flash('Uzdevums un tā mācību notikums dzēsti.', 'success')
        return back('tasks')

    @app.post('/schedule')
    def schedule():
        view = settings()
        start = datetime.fromisoformat(request.form['start'])
        if start.date() not in dates(view) or start.tzinfo:
            raise ValueError('Izvēlies intervālu pašreizējā skatā.')
        store.schedule(int(request.form['task_id']), start.isoformat(), view['start'], view['end'])
        flash('Mācību laiks ieplānots kalendārā. Brīvie intervāli pārrēķināti.', 'success')
        return back('free')

    @app.get('/export.csv')
    def export_csv():
        output = io.StringIO(newline='')
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['Notikums', 'Sākums', 'Beigas', 'Veids', 'Avots'])
        for event in visible_events(settings()):
            values = [event[k] for k in ['title', 'start', 'end', 'kind', 'source']]
            writer.writerow(["'"+v if v.startswith(('=', '+', '-', '@')) else v for v in values])
        return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')), as_attachment=True,
                         download_name='kalendars.csv', mimetype='text/csv')

    @app.get('/backup.db')
    def backup():
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'planner_backup.db'
            store.backup(path)
            content = path.read_bytes()
        return send_file(io.BytesIO(content), as_attachment=True, download_name='planner_backup.db',
                         mimetype='application/octet-stream')

    @app.post('/google/config')
    def config_upload():
        upload = request.files.get('credentials')
        if not upload:
            raise ValueError('Izvēlies Google JSON failu.')
        try:
            config = google.validate_config(json.loads(upload.read().decode('utf-8-sig')))
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError('Fails nav derīgs JSON.') from None
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write; never use the uploaded filename as a path.
        with lock:
            temp_path = config_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    os.chmod(temp_path, 0o600)
                    json.dump(config, f)
                os.replace(temp_path, config_path)
            finally:
                temp_path.unlink(missing_ok=True)
            sessions.clear()
        flash('Google piekļuves fails saglabāts. Tagad vari pieslēgties.', 'success')
        return back('connections')

    def sync(state, view):
        with state['lock']:
            ds = dates(view)
            events = google.load_events(state['credentials'], ds[0], ds[-1])
            store.replace_google(events)
            state['updated'] = f"{ds[0]:%d.%m.%Y} – {ds[-1]:%d.%m.%Y}, atjaunots {datetime.now():%H:%M}"
        flash(f'Ielādēti {len(events)} Google notikumi. Brīvais laiks pārrēķināts.', 'success')

    @app.post('/google/connect')
    def connect_google():
        state = browser_state()
        view = settings()
        if state['credentials'] is not None:
            sync(state, view)
            return back('connections')
        if not config_path.exists():
            raise ValueError('Vispirms augšupielādē Google OAuth Web application JSON failu.')
        config = google.validate_credentials(config_path)
        flow, auth_url, nonce = google.start_flow(config, callback)
        state['pending'] = {'flow': flow, 'state': nonce, 'created': clock.monotonic(), 'view': view}
        return redirect(auth_url, code=303)

    @app.get('/google/callback')
    def google_callback():
        state = browser_state()
        pending = state.pop('pending', None)
        if (not pending or clock.monotonic()-pending['created'] > 600
                or not secrets.compare_digest(request.args.get('state', ''), pending['state'])):
            flash('Pieslēgšanās sesija nav derīga vai ir beigusies. Spied “Pieslēgties ar Google” vēlreiz.', 'error')
            return back('connections')
        if request.args.get('error') or not request.args.get('code'):
            flash('Google piekļuve netika apstiprināta. Vari mēģināt vēlreiz.', 'error')
            return back('connections')
        state['credentials'] = google.exchange(pending['flow'], request.args['code'])
        session['view'] = pending['view']
        sync(state, pending['view'])
        return back('connections')

    @app.post('/google/disconnect')
    def disconnect_google():
        state = browser_state()
        with state['lock']:
            state['credentials'] = None
            state['pending'] = None
            state['updated'] = None
            store.replace_google([])
        flash('Atvienots. Lokālie Google notikumi dzēsti; tavs Google kalendārs nav mainīts.', 'success')
        return back('connections')

    @app.errorhandler(ValueError)
    def bad_value(error):
        flash(str(error), 'error')
        return back('connections' if request.path.startswith('/google') else None)

    @app.errorhandler(sqlite3.IntegrityError)
    def duplicate(error):
        flash('Šāds ieraksts jau pastāv vai uzdevums jau ieplānots.', 'error')
        return back()

    @app.errorhandler(sqlite3.Error)
    @app.errorhandler(OSError)
    def storage_error(error):
        flash('Neizdevās nolasīt vai saglabāt datus. Pārbaudi mapes rakstīšanas tiesības un brīvo vietu.', 'error')
        return back()

    @app.errorhandler(400)
    @app.errorhandler(413)
    def bad_request(error):
        if isinstance(error, SecurityError):
            return 'Nederīga servera adrese.', 400
        return render_template('error.html', message='Pieprasījums nav derīgs vai fails pārsniedz 128 KB. Atgriezies un atjauno lapu.'), error.code

    return app


if __name__ == '__main__':
    from waitress import serve
    application = create_app()
    address = public_url()
    print(f'Plānotājs: {address}', flush=True)
    print('Codespaces: PORTS → 8000 → Open in Browser (Private). Apturēt: Ctrl+C.', flush=True)
    serve(application, host='0.0.0.0' if os.environ.get('CODESPACES') == 'true' else '127.0.0.1', port=8000, threads=4)
