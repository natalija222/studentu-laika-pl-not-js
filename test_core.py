import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from core import free_intervals

TZ = ZoneInfo('Europe/Riga')

class FreeTimeTests(unittest.TestCase):
    def test_overlaps_and_gaps(self):
        events = [
            {'start': datetime(2026, 10, 29, 9, 0, tzinfo=TZ), 'end': datetime(2026, 10, 29, 11, 0, tzinfo=TZ)},
            {'start': datetime(2026, 10, 29, 10, 30, tzinfo=TZ), 'end': datetime(2026, 10, 29, 12, 0, tzinfo=TZ)},
            {'start': datetime(2026, 10, 29, 14, 0, tzinfo=TZ), 'end': datetime(2026, 10, 29, 15, 0, tzinfo=TZ)},
        ]
        result = free_intervals(events, date(2026, 10, 29), 8, 17, 30, TZ)
        self.assertEqual([(a.strftime('%H:%M'), b.strftime('%H:%M')) for a,b in result],
                         [('08:00','09:00'),('12:00','14:00'),('15:00','17:00')])

    def test_no_events(self):
        result = free_intervals([], date(2026,10,29), 8, 20, 30, TZ)
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main()
