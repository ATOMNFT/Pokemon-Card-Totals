import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app

class Counts(unittest.TestCase):
    def test_unique_ids(self):
        with patch('app.urlopen', return_value=io.BytesIO(b'[{"id":"a"},{"id":"a"},{"id":"b"}]')):
            self.assertEqual(app.count_cards('ja'), 2)
    def test_invalid_list(self):
        for content in (b'[]', b'{}', b'[{"name":"bad"}]'):
            with patch('app.urlopen', return_value=io.BytesIO(content)):
                with self.assertRaises(ValueError): app.count_cards('en')
    def test_partial_failure_keeps_cached_total_and_timestamp(self):
        with tempfile.TemporaryDirectory() as folder, patch('app.CACHE', Path(folder)/'totals.json'):
            app.CACHE.write_text(json.dumps({'languages':{'ja':{'total':23,'updated_at':'old'}}}))
            def fetch(lang):
                if lang=='ja': raise OSError('offline')
                return 45
            with patch('app.count_cards', side_effect=fetch): result=app.refresh()
            self.assertEqual(result['languages']['en']['total'],45)
            self.assertEqual(result['languages']['ja']['total'],23)
            self.assertEqual(result['languages']['ja']['updated_at'],'old')
            self.assertTrue(result['languages']['ja']['error'])
            self.assertEqual(app.read_cache(),result)
            with patch('app.count_cards', return_value=50): result=app.refresh()
            self.assertIsNone(result['languages']['ja']['error'])

if __name__=='__main__': unittest.main()

class Changes(unittest.TestCase):
    def test_delta_baselines_and_failures(self):
        with tempfile.TemporaryDirectory() as folder, patch('app.CACHE', Path(folder)/'totals.json'):
            with patch('app.count_cards', return_value=100): result=app.refresh()
            self.assertIsNone(result['languages']['en']['delta'])
            with patch('app.count_cards', return_value=124): result=app.refresh()
            self.assertEqual(result['languages']['en']['delta'],24)
            with patch('app.count_cards', side_effect=OSError()): app.refresh()
            with patch('app.count_cards', return_value=130): result=app.refresh()
            self.assertEqual(result['languages']['en']['delta'],6)
            with patch('app.count_cards', return_value=120): result=app.refresh()
            self.assertEqual(result['languages']['en']['delta'],-10)
            with patch('app.count_cards', return_value=120): result=app.refresh()
            self.assertEqual(result['languages']['en']['delta'],0)
