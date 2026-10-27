"""Google Calendar lasīšana tīmekļa saskarnei. Pilnvaras glabājas servera atmiņā."""
import json
from datetime import datetime, time, timedelta
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']


def validate_config(data):
    if isinstance(data, dict) and 'installed' in data:
        raise ValueError('Šai pārlūka versijai vajadzīgs Google OAuth Web application JSON, nevis Desktop app. Skati norādes sadaļā Savienojumi.')
    try:
        client = data['web']
        if (not client.get('client_id') or not client.get('client_secret')
                or client.get('auth_uri') not in {'https://accounts.google.com/o/oauth2/auth', 'https://accounts.google.com/o/oauth2/v2/auth'}
                or client.get('token_uri') != 'https://oauth2.googleapis.com/token'
                or not isinstance(client.get('redirect_uris'), list)):
            raise ValueError()
        return data
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ValueError('Izvēlies Google Cloud OAuth Web application JSON failu ar reģistrētu atgriešanās adresi.') from None


def validate_credentials(path):
    try:
        return validate_config(json.loads(Path(path).read_text(encoding='utf-8')))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('Fails nav derīgs Google JSON fails.') from None


def start_flow(config, redirect_uri):
    from google_auth_oauthlib.flow import Flow
    validate_config(config)
    if redirect_uri not in config['web']['redirect_uris']:
        raise ValueError('JSON failā nav šīs atgriešanās adreses. Pievieno ekrānā norādīto adresi Google klienta Authorized redirect URIs un lejupielādē JSON vēlreiz.')
    flow = Flow.from_client_config(config, SCOPES, autogenerate_code_verifier=True)
    flow.redirect_uri = redirect_uri
    url, state = flow.authorization_url(access_type='offline', prompt='select_account')
    return flow, url, state


def exchange(flow, code):
    try:
        flow.fetch_token(code=code, timeout=30)
        credentials = flow.credentials
        if not credentials.has_scopes(SCOPES):
            raise ValueError()
        return credentials
    except Exception:
        raise ValueError('Google autorizāciju neizdevās pabeigt. Mēģini pieslēgties vēlreiz un piešķir notikumu lasīšanas atļauju.') from None


def load_events(credentials, first, last):
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError
    import httplib2
    try:
        http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=30))
        service = build('calendar', 'v3', http=http, cache_discovery=False)
        try:
            return fetch_events(service, first, last)
        finally:
            service.close()
    except RefreshError:
        raise ValueError('Google sesija beigusies. Atvieno kontu un pieslēdzies vēlreiz.') from None
    except HttpError as exc:
        raise ValueError(f'Google API kļūda ({exc.resp.status}). Pārbaudi Calendar API un lasīšanas atļauju. Iepriekšējais imports saglabāts.') from None
    except (ValueError, KeyError):
        raise ValueError('Google notikumu dati nav derīgi. Iepriekšējais imports saglabāts.') from None
    except Exception:
        raise ValueError('Google dati nav pieejami. Pārbaudi savienojumu un mēģini vēlreiz. Iepriekšējais imports saglabāts.') from None


def normalize(item):
    """Expanded recurring events; transparent/declined events do not block time."""
    if item.get('status') == 'cancelled' or item.get('transparency') == 'transparent':
        return None
    if any(a.get('self') and a.get('responseStatus') == 'declined' for a in item.get('attendees', [])):
        return None
    def parse(value):
        if 'dateTime' in value:
            dt = datetime.fromisoformat(value['dateTime'].replace('Z', '+00:00'))
            if dt.tzinfo is None:
                raise ValueError('Google notikumam trūkst laika joslas. Dati nav atjaunoti.')
            return dt.astimezone().replace(tzinfo=None)
        return datetime.combine(datetime.fromisoformat(value['date']).date(), time.min)
    start, end = parse(item['start']), parse(item['end'])
    if end <= start:
        raise ValueError('Google notikumam ir nederīgs ilgums. Dati nav atjaunoti.')
    return {'title':str(item.get('summary') or 'Bez nosaukuma')[:150],
            'start':start.isoformat(timespec='seconds'), 'end':end.isoformat(timespec='seconds')}


def fetch_events(service, first, last):
    """Fetch every page before replacing the local Google snapshot."""
    lower=datetime.combine(first,time.min).astimezone().isoformat()
    upper=datetime.combine(last+timedelta(days=1),time.min).astimezone().isoformat()
    result, page = [], None
    while True:
        response=service.events().list(calendarId='primary',timeMin=lower,timeMax=upper,
            singleEvents=True,orderBy='startTime',showDeleted=False,maxResults=2500,
            pageToken=page).execute(num_retries=1)
        for item in response.get('items',[]):
            event=normalize(item)
            if event:result.append(event)
        page=response.get('nextPageToken')
        if not page:return result
