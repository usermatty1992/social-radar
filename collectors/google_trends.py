"""Read the official TW Trending Now RSS. No HTML scraping or guessed fields."""
import hashlib
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

FEED_URL = 'https://trends.google.com/trending/rss?geo=TW'
HT = '{https://trends.google.com/trending/rss}'

def public_url(value):
    value = (value or '').strip()
    parts = urlsplit(value)
    return value if parts.scheme in ('https', 'http') and parts.hostname and not parts.username and not parts.password else ''

def stable_id(title):
    canonical = ' '.join(unicodedata.normalize('NFKC', title).casefold().split())
    return 'gt_' + hashlib.sha256(('google_trends:TW:' + canonical).encode()).hexdigest()[:24]

def parse_rss(payload):
    if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise ValueError('Unexpected XML declaration')
    root = ET.fromstring(payload)
    channel = root.find('channel')
    if root.tag != 'rss' or channel is None:
        raise ValueError('RSS format changed: missing rss/channel')
    items = channel.findall('item')
    if len(items) > 500:
        raise ValueError('Unexpected RSS item count')
    results = {}
    for item in items:
        title = (item.findtext('title') or '').strip()
        if not title or len(title) > 300:
            raise ValueError('RSS item has no valid title')
        date_text = item.findtext('pubDate')
        published = None
        if date_text:
            date = parsedate_to_datetime(date_text)
            if date.tzinfo is None:
                raise ValueError('RSS date has no timezone')
            published = date.astimezone(timezone.utc).isoformat()
        news = []
        for entry in item.findall(HT + 'news_item')[:5]:
            url = public_url(entry.findtext(HT + 'news_item_url'))
            headline = (entry.findtext(HT + 'news_item_title') or '').strip()
            if url and headline:
                news.append({'title': headline[:300], 'url': url, 'publisher': (entry.findtext(HT + 'news_item_source') or '')[:100]})
        identifier = stable_id(title)
        results[identifier] = {
            'id': identifier, 'title': title, 'keywords': [title], 'category': '其他',
            'source': 'google_trends', 'source_url': public_url(item.findtext('link')) or FEED_URL,
            'source_published_at': published, 'trend_started_at': None, 'status': 'unknown',
            'search_volume_label': (item.findtext(HT + 'approx_traffic') or '').strip() or None,
            'rank': None, 'related_posts': [], 'related_news': news,
        }
    return list(results.values())

def fetch_topics():
    request = urllib.request.Request(FEED_URL, headers={'User-Agent': 'SocialRadar/1.0 (+Google-Trends-RSS; personal research)', 'Accept': 'application/rss+xml, application/xml'})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(5 * 1024 * 1024 + 1)
        if len(payload) > 5 * 1024 * 1024:
            raise ValueError('RSS is too large')
    return parse_rss(payload)
