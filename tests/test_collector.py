import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.google_trends import parse_rss, stable_id
from scripts.update_data import update
from scripts.validate_data import validate_directory

RSS = b'''<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss"><channel><item><title>Test Beer</title><link>https://trends.google.com/trending/rss?geo=TW</link><pubDate>Tue, 13 Oct 2026 14:00:00 -0700</pubDate><ht:approx_traffic>500+</ht:approx_traffic><ht:news_item><ht:news_item_title>Public headline</ht:news_item_title><ht:news_item_url>https://example.com/article</ht:news_item_url><ht:news_item_source>News</ht:news_item_source></ht:news_item></item></channel></rss>'''
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = (PROJECT_ROOT / 'test-results').resolve()
assert TEST_ROOT.is_relative_to(PROJECT_ROOT), 'Temporary test data must remain within the project'
TEST_ROOT.mkdir(exist_ok=True)

class CollectorTests(unittest.TestCase):
    def test_actual_rss_fields_only(self):
        t = parse_rss(RSS)[0]
        self.assertEqual(t['search_volume_label'], '500+')
        self.assertEqual(t['source_published_at'], '2026-10-13T21:00:00+00:00')
        self.assertIsNone(t['trend_started_at'])
        self.assertIsNone(t['rank'])
        self.assertEqual(t['status'], 'unknown')
        self.assertEqual(len(t['related_news']), 1)

    def test_stable_ids_and_deduplication(self):
        self.assertEqual(stable_id('Test  Beer'), stable_id('test beer'))
        twice = RSS.replace(b'</channel>', RSS.split(b'<channel>')[1].split(b'</channel>')[0] + b'</channel>')
        self.assertEqual(len(parse_rss(twice)), 1)

    def test_empty_feed_is_valid_but_invalid_format_is_not(self):
        self.assertEqual(parse_rss(b'<rss><channel/></rss>'), [])
        for xml in (b'<html/>', b'<rss><channel><item/></channel></rss>', b'<!DOCTYPE rss><rss><channel/></rss>'):
            with self.assertRaises(Exception):
                parse_rss(xml)

    def test_news_urls_are_validated(self):
        unsafe = RSS.replace(b'https://example.com/article', b'javascript:alert(1)')
        self.assertEqual(parse_rss(unsafe)[0]['related_news'], [])

    def test_failed_source_preserves_all_last_good_data(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as folder:
            root = Path(folder)
            now = datetime(2026, 10, 14, 3, 17, tzinfo=timezone.utc)
            self.assertTrue(update(root, lambda: parse_rss(RSS), now))
            previous = {p.name: p.read_bytes() for p in (root / 'latest.json', root / 'topics.json')}
            def fail():
                raise RuntimeError('a-secret-that-must-not-be-logged')
            self.assertFalse(update(root, fail, now + timedelta(hours=6)))
            for p in (root / 'latest.json', root / 'topics.json'):
                self.assertEqual(p.read_bytes(), previous[p.name])
            status = json.loads((root / 'status.json').read_text(encoding='utf-8'))
            self.assertEqual(status['sources']['google_trends']['last_success_at'], now.isoformat())
            self.assertNotIn('a-secret', (root / 'status.json').read_text(encoding='utf-8'))
            validate_directory(root)

    def test_invalid_topic_cannot_replace_valid_data(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as folder:
            root = Path(folder)
            now = datetime(2026, 10, 14, 3, 17, tzinfo=timezone.utc)
            update(root, lambda: parse_rss(RSS), now)
            previous = (root / 'latest.json').read_bytes()
            broken = parse_rss(RSS)
            broken[0]['rank'] = 1
            self.assertFalse(update(root, lambda: broken, now + timedelta(hours=6)))
            self.assertEqual((root / 'latest.json').read_bytes(), previous)

    def test_daily_file_retains_multiple_snapshots_and_first_seen(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as folder:
            root = Path(folder)
            now = datetime(2026, 10, 14, 3, 17, tzinfo=timezone.utc)
            update(root, lambda: parse_rss(RSS), now)
            update(root, lambda: parse_rss(RSS), now + timedelta(hours=6))
            latest = json.loads((root / 'latest.json').read_text(encoding='utf-8'))['topics'][0]
            self.assertEqual(latest['first_seen_at'], now.isoformat())
            self.assertEqual(latest['snapshot_count'], 2)
            history = json.loads((root / 'history' / '2026-10-14.json').read_text(encoding='utf-8'))
            self.assertEqual(len(history['snapshots']), 2)
            validate_directory(root)

    def test_retention_removes_only_old_daily_files(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as folder:
            root = Path(folder)
            now = datetime(2026, 10, 14, 3, 17, tzinfo=timezone.utc)
            update(root, lambda: parse_rss(RSS), now)
            old = root / 'history' / '2026-01-01.json'
            old.write_text('{}')
            update(root, lambda: [], now + timedelta(hours=6))
            self.assertFalse(old.exists())
            self.assertEqual(json.loads((root / 'latest.json').read_text(encoding='utf-8'))['topics'], [])

if __name__ == '__main__':
    unittest.main()
