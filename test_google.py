import unittest
import tempfile
from pathlib import Path
from datetime import date, datetime
from unittest.mock import MagicMock
from google_calendar import normalize, fetch_events, validate_credentials
from core import Store

class GoogleTests(unittest.TestCase):
    def item(self):
        return {'summary':'Lekcija','start':{'dateTime':'2030-01-07T09:00:00+02:00'},'end':{'dateTime':'2030-01-07T10:00:00+02:00'}}
    def test_timezone(self):
        expected=datetime.fromisoformat('2030-01-07T09:00:00+02:00').astimezone().replace(tzinfo=None).isoformat()
        self.assertEqual(normalize(self.item())['start'],expected)
    def test_all_day_exclusive_end(self):
        e=normalize({'start':{'date':'2030-01-07'},'end':{'date':'2030-01-08'}})
        self.assertEqual(e['end'],'2030-01-08T00:00:00')
    def test_nonblocking(self):
        for extra in [{'status':'cancelled'},{'transparency':'transparent'},{'attendees':[{'self':True,'responseStatus':'declined'}]}]:
            self.assertIsNone(normalize(dict(self.item(),**extra)))
    def test_pages(self):
        service=MagicMock()
        service.events().list().execute.side_effect=[{'items':[self.item()],'nextPageToken':'next'},{'items':[]}]
        self.assertEqual(len(fetch_events(service,date(2030,1,7),date(2030,1,13))),1)
        self.assertEqual(service.events().list.call_args.kwargs['pageToken'],'next')
        self.assertTrue(service.events().list.call_args.kwargs['singleEvents'])
    def test_failed_page(self):
        service=MagicMock()
        service.events().list().execute.side_effect=[{'items':[self.item()],'nextPageToken':'next'},OSError('offline')]
        with self.assertRaises(OSError):fetch_events(service,date(2030,1,7),date(2030,1,13))
    def test_snapshot_update_delete_and_manual_preservation(self):
        with tempfile.TemporaryDirectory() as d:
            db=Store(Path(d)/'db')
            db.add_event('Manual','2030-01-07T09:00','2030-01-07T10:00')
            e=normalize(self.item())
            db.replace_google([e])
            db.replace_google([e])
            self.assertEqual(len(db.events()),2)
            e['title']='Changed'
            db.replace_google([e])
            self.assertIn('Changed',[x['title'] for x in db.events()])
            db.replace_google([])
            self.assertEqual([x['title'] for x in db.events()],['Manual'])
    def test_invalid_snapshot_preserves_old(self):
        with tempfile.TemporaryDirectory() as d:
            db=Store(Path(d)/'db')
            db.replace_google([normalize(self.item())])
            with self.assertRaises(ValueError):db.replace_google([{'title':'Broken','start':'bad','end':'bad'}])
            self.assertEqual(len(db.events()),1)
    def test_wrong_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'credentials.json'
            p.write_text('{"web":{}}')
            with self.assertRaises(ValueError):validate_credentials(p)

if __name__=='__main__':unittest.main()
