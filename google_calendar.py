"""Read-only Google Calendar. Tokens stay in process memory, never in files."""
import json
from datetime import datetime, time, timedelta
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']


def validate_credentials(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        client = data['installed']
        if (not client.get('client_id') or not client.get('client_secret')
                or client.get('auth_uri') != 'https://accounts.google.com/o/oauth2/auth'
                or client.get('token_uri') != 'https://oauth2.googleapis.com/token'):
            raise ValueError()
        return data
    except (KeyError, ValueError, TypeError):
        raise ValueError('Izvēlies no Google Cloud lejupielādēto OAuth Desktop app JSON failu.') from None


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


class GoogleCalendar:
    def __init__(self):
        self.credentials = None

    def disconnect(self):
        self.credentials = None

    def fetch(self, credentials_path, first, last):
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google_auth_httplib2 import AuthorizedHttp
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            from google.auth.exceptions import RefreshError
            import httplib2
        except ImportError:
            raise ValueError('Vispirms palaid INSTALLET_GOOGLE.bat vai: python -m pip install -r requirements.txt') from None
        try:
            if self.credentials and self.credentials.expired:
                try:
                    self.credentials.refresh(Request())
                except RefreshError:
                    self.credentials=None
            if not self.credentials or not self.credentials.valid:
                config=validate_credentials(credentials_path)
                flow=InstalledAppFlow.from_client_config(config, SCOPES)
                self.credentials=flow.run_local_server(host='localhost',port=0,
                    timeout_seconds=180,prompt='select_account',
                    authorization_prompt_message='Pieslēdzies Google kontam atvērtajā pārlūkā.',
                    success_message='Savienojums apstiprināts. Vari aizvērt šo cilni un atgriezties plānotājā.')
            http=AuthorizedHttp(self.credentials,http=httplib2.Http(timeout=30))
            service=build('calendar','v3',http=http,cache_discovery=False)
            try:return fetch_events(service,first,last)
            finally:service.close()
        except HttpError as exc:
            raise ValueError(f'Google API kļūda ({exc.resp.status}). Pārbaudi, vai ieslēgts Calendar API un piešķirta kalendāra lasīšanas atļauja. Iepriekšējie dati saglabāti.') from None
        except (ValueError,FileNotFoundError):raise
        except Exception:
            raise ValueError('Savienojums neizdevās vai pieslēgšanās netika pabeigta 3 minūtēs. Pārbaudi internetu un Google testētāja kontu, tad mēģini vēlreiz. Iepriekšējie dati saglabāti.') from None
