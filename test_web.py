import io
import json
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from urllib.parse import urlsplit, parse_qs
from app import create_app
from core import Store
from google_calendar import validate_config, start_flow

CONFIG={'web':{'client_id':'demo.apps.googleusercontent.com','client_secret':'test-secret',
              'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token',
              'redirect_uris':['http://localhost:8000/google/callback']}}

class WebTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.db=Path(self.folder.name)/'planner.db'
        self.config=Path(self.folder.name)/'credentials.json'
        self.app=create_app(self.db,self.config,base_url='http://localhost:8000')
        self.app.config['TESTING']=True
        self.client=self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as s:
            self.csrf=s['csrf'];self.sid=s['sid']
        self.day=(date.today()+timedelta(days=14)).isoformat()
        self.post('/view', {'day':self.day,'period':'day','start':'08:00','end':'22:00','minimum':'60'})
    def tearDown(self):self.folder.cleanup()
    def post(self,path,data=None,**kwargs):
        return self.client.post(path,data={'csrf':self.csrf,**(data or {})},**kwargs)
    def test_all_pages_and_assets(self):
        for tab in ['calendar','free','tasks','connections']:
            r=self.client.get('/?tab='+tab)
            self.assertEqual(r.status_code,200)
            self.assertIn(b'<html lang="lv">',r.data)
        with self.client.get('/static/style.css') as response:
            self.assertEqual(response.status_code,200)
    def test_csrf(self):
        self.assertEqual(self.client.post('/demo').status_code,400)
        self.assertEqual(Store(self.db).events(),[])
    def test_event_and_delete(self):
        self.post('/events',{'title':'Lekcija','start':self.day+'T09:00','end':self.day+'T10:00','kind':'Lekcija'})
        e=Store(self.db).events()[0]
        self.assertIn('Lekcija',self.client.get('/').text)
        self.post(f"/events/{e['id']}/delete")
        self.assertEqual(Store(self.db).events(),[])
    def test_invalid_event(self):
        r=self.post('/events',{'title':'X','start':self.day+'T10:00','end':self.day+'T09:00'},follow_redirects=True)
        self.assertIn('Beigu laikam',r.text)
        self.assertEqual(Store(self.db).events(),[])
    def test_schedule_conflict_and_task_delete(self):
        self.post('/tasks',{'title':'SQL','minutes':60,'deadline':self.day})
        tid=Store(self.db).tasks()[0]['id']
        self.post('/schedule',{'task_id':tid,'start':self.day+'T10:00'})
        self.assertEqual(len(Store(self.db).events()),1)
        r=self.post('/schedule',{'task_id':tid,'start':self.day+'T12:00'},follow_redirects=True)
        self.assertIn('jau ieplānots',r.text)
        self.post(f'/tasks/{tid}/toggle')
        self.assertEqual(Store(self.db).tasks()[0]['done'],1)
        self.post(f'/tasks/{tid}/delete')
        self.assertEqual(Store(self.db).events(),[])
    def test_export_backup_and_persistence(self):
        self.post('/events',{'title':'=formula','start':self.day+'T09:00','end':self.day+'T10:00'})
        r=self.client.get('/export.csv')
        self.assertIn("'=formula",r.data.decode('utf-8-sig'))
        data=self.client.get('/backup.db').data
        self.assertTrue(data.startswith(b'SQLite format 3'))
        other=create_app(self.db,self.config,base_url='http://localhost:8000')
        self.assertEqual(len(other.extensions['store'].events()),1)
    def test_xss_escaped(self):
        self.post('/tasks',{'title':'<script>alert(1)</script>','minutes':60,'deadline':self.day})
        body=self.client.get('/?tab=tasks').text
        self.assertIn('&lt;script&gt;',body)
        self.assertNotIn('<script>alert',body)
    def test_invalid_filter_does_not_replace(self):
        r=self.post('/view',{'day':self.day,'period':'day','start':'22:00','end':'08:00','minimum':60},follow_redirects=True)
        self.assertEqual(r.status_code,200)
        with self.client.session_transaction() as s:self.assertEqual(s['view']['start'],'08:00')
    def test_credentials_upload_and_wrong_type(self):
        r=self.post('/google/config',{'credentials':(io.BytesIO(b'{"installed":{}}'),'desktop.json')},follow_redirects=True)
        self.assertIn('Web application',r.text)
        self.assertFalse(self.config.exists())
        self.post('/google/config',{'credentials':(io.BytesIO(json.dumps(CONFIG).encode()),'client.json')})
        self.assertTrue(self.config.exists())
        self.assertEqual(json.loads(self.config.read_text()),CONFIG)
        self.assertNotIn('test-secret',self.client.get('/?tab=connections').text)
    def test_google_block_local_delete(self):
        Store(self.db).replace_google([{'title':'Google','start':self.day+'T10:00','end':self.day+'T11:00'}])
        eid=Store(self.db).events()[0]['id']
        self.post(f'/events/{eid}/delete')
        self.assertEqual(len(Store(self.db).events()),1)
    def test_google_failed_sync_keeps_snapshot(self):
        db=Store(self.db)
        db.replace_google([{'title':'Old','start':self.day+'T10:00','end':self.day+'T11:00'}])
        self.app.extensions['google_sessions'][self.sid]['credentials']=object()
        with patch('app.google.load_events',side_effect=ValueError('Neizdevās')):
            self.post('/google/connect')
        self.assertEqual(db.events()[0]['title'],'Old')
    def test_oauth_state_rejection(self):
        state=self.app.extensions['google_sessions'][self.sid]
        state['pending']={'flow':object(),'state':'correct','created':__import__('time').monotonic()}
        with patch('app.google.exchange') as exchange:
            self.client.get('/google/callback?code=secret&state=wrong')
            exchange.assert_not_called()
        self.assertIsNone(state['credentials'])
    def test_oauth_callback_and_disconnect(self):
        self.config.write_text(json.dumps(CONFIG))
        with patch('app.google.start_flow',return_value=(object(),'https://accounts.google.com/test','correct')):
            r=self.post('/google/connect')
            self.assertEqual(r.status_code,303)
        payload=[{'title':'Lecture','start':self.day+'T10:00','end':self.day+'T11:00'}]
        with patch('app.google.exchange',return_value=object()),patch('app.google.load_events',return_value=payload):
            self.client.get('/google/callback?code=secret&state=correct')
        self.assertEqual(Store(self.db).events()[0]['title'],'Lecture')
        self.post('/google/disconnect')
        self.assertEqual(Store(self.db).events(),[])
    def test_authorization_parameters(self):
        flow,url,state=start_flow(CONFIG,'http://localhost:8000/google/callback')
        params=parse_qs(urlsplit(url).query)
        self.assertEqual(params['state'],[state])
        self.assertEqual(params['redirect_uri'],CONFIG['web']['redirect_uris'])
        self.assertEqual(params['code_challenge_method'],['S256'])
        self.assertIn('calendar.events.readonly',params['scope'][0])
    def test_redirect_configuration_required(self):
        with self.assertRaises(ValueError):start_flow(CONFIG,'https://different.app.github.dev/google/callback')
    def test_host_check(self):
        self.assertEqual(self.client.get('/',headers={'Host':'evil.example'}).status_code,400)

if __name__=='__main__':unittest.main()
