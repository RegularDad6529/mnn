#!/usr/bin/env python3
"""Fetch Shillandia wave drops and additional dive bar content."""
import json, urllib.request, ssl, re, time
from datetime import datetime, timezone

with open('/home/prenode/.hermes/profiles/themanager/6529_tokens.json') as f:
    jwt = json.load(f)['token']

API = 'https://api.6529.io'
ctx = ssl.create_default_context()

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {jwt}',
                'User-Agent': 'Mozilla/5.0'
            })
            resp = urllib.request.urlopen(req, timeout=30, context=ctx)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return {'error': str(e)}
    return {}

# Shillandia wave
shill_wave_id = 'c143d8f7-d04f-41ec-b0fd-377e61512d71'
week_start_ms = 1789948800000  # Sep 21 2026

print("=== SHILLANDIA WAVE DROPS ===")
shill_data = fetch(f'{API}/api/v2/waves/{shill_wave_id}/drops?limit=200')
s_drops = shill_data.get('drops', [])
print(f"Total drops returned: {len(s_drops)}")
week_shill = []
for d in s_drops:
    ts = d.get('created_at', 0)
    if isinstance(ts, (int, float)) and ts > 1000000000:
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
        content = d.get('content', '')
        if not content and d.get('parts'):
            content = d['parts'][0].get('content', '')
        if ts >= week_start_ms:
            week_shill.append({
                'serial': d.get('serial_no'),
                'author': d.get('author', {}).get('handle', ''),
                'content': content[:500],
                'created_at': dt.strftime('%Y-%m-%d %H:%M')
            })

print(f"Drops this week: {len(week_shill)}")
for d in week_shill[:30]:
    print(f"  {d['created_at']} @{d['author']}: {d['content'][:250]}")
print()

# Also paginate back for more
if s_drops:
    oldest_serial = s_drops[-1].get('serial_no', 0)
    for page in range(5):
        data2 = fetch(f'{API}/api/waves/{shill_wave_id}/drops?sort_direction=DESC&limit=50&serial_no_less_than={oldest_serial}')
        drops2 = data2.get('drops', [])
        if not drops2:
            break
        for d in drops2:
            ts = d.get('created_at', 0)
            if isinstance(ts, (int, float)) and ts >= week_start_ms:
                content = d.get('content', '')
                if not content and d.get('parts'):
                    content = d['parts'][0].get('content', '')
                dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
                week_shill.append({
                    'serial': d.get('serial_no'),
                    'author': d.get('author', {}).get('handle', ''),
                    'content': content[:500],
                    'created_at': dt.strftime('%Y-%m-%d %H:%M')
                })
        oldest_serial = drops2[-1].get('serial_no', 0)
        oldest_ts = drops2[-1].get('created_at', 0)
        if isinstance(oldest_ts, (int, float)) and oldest_ts < week_start_ms:
            break
        time.sleep(0.3)

print(f"Total Shillandia drops this week (with pagination): {len(week_shill)}")
# Show unique coming soon / active mints
coming_soon = []
active_mints = []
for d in week_shill:
    text = d['content'].lower()
    if any(kw in text for kw in ['coming soon', 'tomorrow', 'next week', 'will mint', 'will drop', 'will release', 'new collection', 'announcing']):
        coming_soon.append(d)
    if any(kw in text for kw in ['transient.xyz/mint/', 'manifold.xyz', 'live', 'now live', 'minting now']):
        active_mints.append(d)

print(f"\nComing Soon: {len(coming_soon)}")
for d in coming_soon[:10]:
    print(f"  {d['created_at']} @{d['author']}: {d['content'][:200]}")

print(f"\nActive Mints: {len(active_mints)}")
for d in active_mints[:10]:
    print(f"  {d['created_at']} @{d['author']}: {d['content'][:200]}")

# Dive bar specific deep dive - look for interesting conversations
print("\n=== DIVE BAR DEEP DIVE ===")
dive_bar = 'b38288e6-ca9d-45ce-8323-3dc5e094f04e'
cursor = None
all_notable_detailed = []
batch_count = 0

# Focus on conversations, debates, notable quotes
deep_keywords = ['tdh', 'drama', 'vote', 'drain', 'hack', 'wallet', 'opensea',
                 'stolen', 'scam', 'drained', 'portfolio', 'strategy', 'sunk cost',
                 'minting', 'marketplace', 'meme lab', 'help6529', 'emma',
                 'newsletter', 'eligibility', 'rep', 'moderation',
                 'pissarides', 'nobel', 'economics', 'book', 'antifragile',
                 'physical', 'shipping', 'marfa', 'art blocks',
                 'new member', 'new here', 'joined', 'introduce',
                 'question', 'how do', 'can someone', 'help me',
                 'squiggle', 'pepe', 'rare pepe', 'museum',
                 'gif', 'static', 'preview', 'upload', 'bug',
                 'allow list', 'allowlist', 'whitelist']

while batch_count < 300:
    if cursor:
        url = f'{API}/api/waves/{dive_bar}/drops?sort_direction=DESC&limit=50&serial_no_less_than={cursor}'
    else:
        url = f'{API}/api/waves/{dive_bar}/drops?sort_direction=DESC&limit=50'
    data = fetch(url)
    drops = data.get('drops', [])
    if not drops:
        break
    
    oldest_ts = drops[-1].get('created_at', 0)
    for d in drops:
        ts = d.get('created_at', 0)
        if isinstance(ts, (int, float)) and ts >= week_start_ms:
            content = d.get('content', '')
            if not content and d.get('parts'):
                content = d['parts'][0].get('content', '')
            author = d.get('author', {}).get('handle', '')
            dt_obj = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            text_lower = content.lower()
            
            # Filter for substantive content (longer posts)
            if len(content) > 100:
                for kw in deep_keywords:
                    if kw in text_lower:
                        all_notable_detailed.append({
                            'date': dt_obj.strftime('%Y-%m-%d %H:%M'),
                            'author': author,
                            'content': content,
                            'keyword': kw,
                            'ts': ts
                        })
                        break
    
    cursor = drops[-1].get('serial_no', 0)
    batch_count += 1
    if isinstance(oldest_ts, (int, float)) and oldest_ts < week_start_ms:
        break
    time.sleep(0.3)

print(f"Deep notable drops: {len(all_notable_detailed)}")

# Group by keyword
from collections import Counter
kw_counts = Counter(d['keyword'] for d in all_notable_detailed)
print("Top keywords:", kw_counts.most_common(15))

# Show the most interesting conversations by keyword
for kw in ['drain', 'hack', 'wallet', 'stolen', 'scam', 'portfolio', 'strategy', 'sunk cost',
           'pissarides', 'nobel', 'economics', 'book', 'antifragile', 'physical', 'shipping',
           'marfa', 'squiggle', 'pepe', 'rare pepe', 'museum',
           'static', 'preview', 'upload', 'bug',
           'emma', 'newsletter', 'eligibility', 'rep', 'moderation',
           'new here', 'joined', 'introduce', 'question', 'how do', 'help me',
           'allow list', 'allowlist']:
    items = [d for d in all_notable_detailed if d['keyword'] == kw]
    if items:
        print(f"\n  --- {kw} ({len(items)} drops) ---")
        for item in items[:4]:
            print(f"  [{item['date']}] @{item['author']}: {item['content'][:300]}")
            print()