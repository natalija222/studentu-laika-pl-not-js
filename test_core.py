"""Palaišana: python -m unittest -v"""
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from core import Store, free_slots

DAY=date(2030,1,7)

def event(a,b):
    return {'start':f'2030-01-07T{a}', 'end':f'2030-01-07T{b}'}

def result(events,minimum=60):
    return [(a.strftime('%H:%M'),b.strftime('%H:%M')) for a,b in free_slots(events,DAY,'08:00','18:00',minimum)]

class IntervalTests(unittest.TestCase):
    def test_empty_day(self):
        self.assertEqual(result([]),[('08:00','18:00')])
    def test_one_event(self):
        self.assertEqual(result([event('10:00','12:00')]),[('08:00','10:00'),('12:00','18:00')])
    def test_overlapping(self):
        self.assertEqual(result([event('10:00','13:00'),event('12:00','15:00')]),[('08:00','10:00'),('15:00','18:00')])
    def test_nested(self):
        self.assertEqual(result([event('10:00','15:00'),event('11:00','12:00')]),[('08:00','10:00'),('15:00','18:00')])
    def test_adjacent(self):
        self.assertEqual(result([event('08:00','12:00'),event('12:00','18:00')]),[])
    def test_all_day(self):
        self.assertEqual(result([event('00:00','23:59')]),[])
    def test_cross_midnight(self):
        self.assertEqual(result([{'start':'2030-01-06T23:00','end':'2030-01-07T10:00'}]),[('10:00','18:00')])
    def test_outside_day(self):
        self.assertEqual(result([event('05:00','07:00'),event('19:00','20:00')]),[('08:00','18:00')])
    def test_duration_threshold(self):
        self.assertEqual(result([event('09:00','17:30')],60),[('08:00','09:00')])
    def test_unsorted(self):
        self.assertEqual(result([event('14:00','16:00'),event('09:00','12:00')]),[('08:00','09:00'),('12:00','14:00'),('16:00','18:00')])
    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):free_slots([],DAY,'22:00','08:00')

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'planner.db'
        self.db=Store(self.path)
        self.day=(datetime.now()+timedelta(days=7)).date().isoformat()
    def tearDown(self):self.temp.cleanup()
    def test_persistence(self):
        self.db.add_event('Lekcija',self.day+'T09:00',self.day+'T10:00')
        self.assertEqual(Store(self.path).events()[0]['title'],'Lekcija')
    def test_demo_idempotent(self):
        self.assertEqual(self.db.seed(DAY),9)
        self.assertEqual(self.db.seed(DAY),0)
        self.assertEqual(len(self.db.events()),9)
    def test_schedule_and_conflict(self):
        self.db.add_task('SQL darbs',90,self.day)
        task=self.db.tasks()[0]['id']
        self.db.schedule(task,self.day+'T10:00')
        self.assertEqual(self.db.events()[0]['end'],self.day+'T11:30')
        self.db.add_task('Cits darbs',60,self.day)
        with self.assertRaises(ValueError):self.db.schedule(self.db.tasks()[1]['id'],self.day+'T11:00')
        with self.assertRaises(ValueError):self.db.schedule(task,self.day+'T14:00')
        self.assertEqual(len(self.db.events()),1)
    def test_deadline(self):
        self.db.add_task('Darbs',60,'2000-01-01')
        with self.assertRaises(ValueError):self.db.schedule(self.db.tasks()[0]['id'],self.day+'T10:00')
        self.assertEqual(self.db.events(),[])
    def test_delete_releases_slot(self):
        self.db.add_task('Darbs',60,self.day)
        self.db.schedule(self.db.tasks()[0]['id'],self.day+'T10:00')
        self.db.delete_event(self.db.events()[0]['id'])
        self.assertIsNone(self.db.tasks()[0]['planned'])
    def test_task_cascade(self):
        self.db.add_task('Darbs',60,self.day)
        task=self.db.tasks()[0]['id']
        self.db.schedule(task,self.day+'T10:00')
        self.db.delete_task(task)
        self.assertEqual(self.db.events(),[])
    def test_validation(self):
        for a,b in [('10:00','09:00'),('10:00','10:00')]:
            with self.assertRaises(ValueError):self.db.add_event('X',self.day+'T'+a,self.day+'T'+b)
        with self.assertRaises(ValueError):self.db.add_task('X',0,self.day)
        with self.assertRaises(ValueError):self.db.add_task('',60,self.day)
    def test_backup(self):
        self.db.add_task('Saglabāts',60,self.day)
        dest=Path(self.temp.name)/'backup.db'
        self.db.backup(dest)
        self.assertEqual(Store(dest).tasks()[0]['title'],'Saglabāts')
    def test_completed_task(self):
        self.db.add_task('Darbs',60,self.day)
        task=self.db.tasks()[0]['id']
        self.db.toggle_task(task)
        with self.assertRaises(ValueError):self.db.schedule(task,self.day+'T10:00')
        self.db.toggle_task(task)
        self.assertEqual(self.db.tasks()[0]['done'],0)

if __name__=='__main__': unittest.main()
