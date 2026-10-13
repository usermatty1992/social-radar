import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from collectors.google_trends import fetch_topics

def read(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def update(data_dir, fetch=fetch_topics, now=None):
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat()
    status = read(data_dir / 'status.json', {'schema_version': 1, 'sources': {}})
    sources = status.setdefault('sources', {})
    previous_success = sources.get('google_trends', {}).get('last_success_at')
    try:
        topics = fetch()
        if not isinstance(topics, list):
            raise ValueError('Collector must return a list')
        indexed = read(data_dir / 'topics.json', {'topics': []})['topics']
        indexed = {t['id']: t for t in indexed if datetime.fromisoformat(t['last_seen_at']) >= now - timedelta(days=30)}
        for topic in topics:
            old = indexed.get(topic['id'])
            topic.update(first_seen_at=old['first_seen_at'] if old else stamp, last_seen_at=stamp, collected_at=stamp, snapshot_count=(old['snapshot_count'] if old else 0) + 1)
            indexed[topic['id']] = topic
        latest = {'schema_version': 1, 'collected_at': stamp, 'source': 'google_trends', 'topics': topics}
        from scripts.validate_data import validate_latest, validate_topic
        validate_latest(latest)
        for topic in indexed.values():
            validate_topic(topic)
        day = now.astimezone(timezone(timedelta(hours=8))).date().isoformat()
        history_path = data_dir / 'history' / (day + '.json')
        history = read(history_path, {'schema_version': 1, 'date': day, 'snapshots': []})
        history['snapshots'].append({'collected_at': stamp, 'topics': topics})
        # Validation happens before any success-data file is replaced.
        write(history_path, history)
        write(data_dir / 'latest.json', latest)
        write(data_dir / 'topics.json', {'schema_version': 1, 'updated_at': stamp, 'topics': list(indexed.values())})
        sources['google_trends'] = {'enabled': True, 'state': 'ok', 'last_attempt_at': stamp, 'last_success_at': stamp, 'count': len(topics), 'message': 'Google Trends 台灣 RSS；未提供活躍狀態與相關搜尋詞。'}
        success = True
    except Exception:
        # Do not put server response bodies, credentials, or exception payloads in public logs.
        sources['google_trends'] = {'enabled': True, 'state': 'error', 'last_attempt_at': stamp, 'last_success_at': previous_success, 'message': '本次擷取或格式驗證失敗，保留最近有效資料；請查看來源是否恢復。'}
        success = False
    enabled = os.getenv('ENABLE_THREADS', 'false').lower() == 'true'
    sources['threads'] = {'enabled': False, 'state': 'not_connected', 'last_success_at': None, 'message': '尚未完成 Meta 授權與資料保留驗證，未自動蒐集。' if not enabled else '設定要求啟用，但授權尚未驗證；已停用，未蒐集任何貼文。'}
    sources['instagram'] = {'enabled': False, 'state': 'manual_only', 'last_success_at': None, 'message': '僅支援手動收藏公開貼文連結。'}
    status.update(schema_version=1, checked_at=stamp, timezone='Asia/Taipei', schedule_local=['05:17', '11:17', '17:17', '23:17'])
    write(data_dir / 'status.json', status)
    for path in (data_dir / 'history').glob('*.json'):
        if path.stem < (now.astimezone(timezone(timedelta(hours=8))).date() - timedelta(days=29)).isoformat():
            path.unlink()
    return success

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    ok = update(args.data_dir)
    print('Google Trends: success' if ok else 'Google Trends: failed; retained last valid data')
    sys.exit(0 if ok else 1)
