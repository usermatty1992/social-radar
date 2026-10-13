import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

def date(value):
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, 'Date must include timezone'

def validate_topic(t):
    assert isinstance(t, dict) and isinstance(t['id'], str) and t['id'].startswith('gt_')
    assert isinstance(t['title'], str) and 0 < len(t['title']) <= 300
    assert t['source'] == 'google_trends'
    assert isinstance(t['keywords'], list) and all(isinstance(k, str) for k in t['keywords'])
    assert urlsplit(t['source_url']).scheme in ('https', 'http')
    assert t['rank'] is None and t['status'] == 'unknown'
    assert t['trend_started_at'] is None
    assert t['search_volume_label'] is None or isinstance(t['search_volume_label'], str)
    assert isinstance(t['snapshot_count'], int) and t['snapshot_count'] >= 1
    for key in ('first_seen_at', 'last_seen_at', 'collected_at'):
        date(t[key])
    if t['source_published_at']:
        date(t['source_published_at'])
    for article in t['related_news']:
        assert isinstance(article['title'], str) and urlsplit(article['url']).scheme in ('https', 'http')
    assert t['related_posts'] == []

def validate_latest(data):
    assert data['schema_version'] == 1 and isinstance(data['topics'], list)
    date(data['collected_at'])
    identifiers = []
    for topic in data['topics']:
        validate_topic(topic)
        identifiers.append(topic['id'])
    assert len(identifiers) == len(set(identifiers)), 'Duplicate topic IDs'

def validate_directory(root):
    validate_latest(json.loads((root / 'latest.json').read_text(encoding='utf-8')))
    indexed = json.loads((root / 'topics.json').read_text(encoding='utf-8'))
    for topic in indexed['topics']:
        validate_topic(topic)
    for path in (root / 'history').glob('*.json'):
        history = json.loads(path.read_text(encoding='utf-8'))
        assert history['date'] == path.stem
        for snapshot in history['snapshots']:
            validate_latest({'schema_version': 1, **snapshot})
    status = json.loads((root / 'status.json').read_text(encoding='utf-8'))
    assert set(status['sources']) == {'google_trends', 'threads', 'instagram'}
    assert status['sources']['threads']['enabled'] is False
    assert status['sources']['instagram']['enabled'] is False
    print('PASS: public JSON, dates, topic IDs, history, disabled sources')

if __name__ == '__main__':
    validate_directory(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'data')
