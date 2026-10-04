#!/usr/bin/env python3
"""Fetch all data needed for weekly MNN report."""
import json, urllib.request, ssl, re, time
from datetime import datetime, timezone, timedelta

# Load token
with open('/home/prenode/.hermes/profiles/themanager/6529_tokens.json') as f:
    jwt = json.load(f)['token']

API = 'https://api.6529.io'
ssl_ctx = ssl.create_default_context()

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {jwt}',
                'User-Agent': 'Mozilla/5.0'
            })
            resp = urllib.request.urlopen(req, timeout=30, context=ssl_ctx)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return {'error': str(e)}
    return {}

# Compute week boundaries
today = datetime(2026, 9, 27, tzinfo=timezone.utc)
iso = today.isocalendar()
week_num = iso.week
year = iso.year
# Monday of this ISO week
week_start = today - timedelta(days=today.weekday())
week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
week_end = week_start + timedelta(days=7)

print(f"ISO Week: {year}-W{week_num:02d}")
print(f"Week start: {week_start}")
print(f"Week end: {week_end}")
print(f"Week start ms: {int(week_start.timestamp() * 1000)}")
print()

# 1. GitHub PRs
print("=== GITHUB PRs ===")
try:
    import subprocess
    result = subprocess.run(
        ['gh', 'search', 'prs', '--owner', '6529-Collections', '--merged',
         '--limit', '100', '--json', 'repository,title,number,updatedAt,author',
         '--sort', 'updated'],
        capture_output=True, text=True, timeout=30
    )
    prs = json.loads(result.stdout) if result.stdout else []
    week_prs = []
    for pr in prs:
        dt = datetime.strptime(pr['updatedAt'][:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if week_start <= dt < week_end:
            week_prs.append(pr)
    print(f"Total merged PRs (last 100): {len(prs)}")
    print(f"PRs this week: {len(week_prs)}")
    for pr in week_prs:
        print(f"  {pr['updatedAt'][:10]} #{pr['number']} {pr['author']} - {pr['title']} ({pr['repository']})")
except Exception as e:
    print(f"GitHub error: {e}")
print()

# 2. NFT API for recent cards
print("=== NFT API (recent cards) ===")
nft_data = fetch(f'{API}/api/nfts?collection=0x33FD426905F149f8376e227d0C9D3340AaD17aF1&limit=100&sort=recent')
nfts = nft_data.get('data', [])
print(f"Total NFTs returned: {nft_data.get('count', 0)}")
# Filter to cards from this week or recent
for nft in nfts[:20]:
    card_id = nft.get('id')
    name = nft.get('name', '')
    artist = nft.get('artist', '')
    supply = nft.get('supply', 0)
    mint_price = nft.get('mint_price', 0)
    meta = nft.get('metadata', {})
    attrs = {}
    if meta and 'attributes' in meta:
        for attr in meta['attributes']:
            attrs[attr.get('trait_type', '')] = attr.get('value', '')
    issuance = attrs.get('Issuance Month', '')
    card_type = attrs.get('Type - Card', '')
    print(f"  #{card_id} {name} by {artist} | supply={supply} | issuance={issuance} | type={card_type}")
print()

# 3. Follow The Repo subwaves
print("=== FOLLOW THE REPO SUBWAVES ===")
dev_wave = '49f0e595-ec7c-4235-8695-a527f61b69f4'
subwaves_data = fetch(f'{API}/api/waves/{dev_wave}/subwaves')
subwaves = subwaves_data.get('data', [])
print(f"Subwaves: {len(subwaves)}")
dev_drops_week = []
for sw in subwaves:
    sw_id = sw['id']
    sw_name = sw.get('name', 'unknown')
    drops = fetch(f'{API}/api/waves/{sw_id}/drops?limit=50')
    sw_drops = drops.get('drops', [])
    week_drops = []
    for d in sw_drops:
        ts = d.get('created_at', 0)
        if isinstance(ts, (int, float)) and ts > 1000000000:
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            if week_start <= dt < week_end:
                content = d.get('content', '')
                if not content and d.get('parts'):
                    content = d['parts'][0].get('content', '')
                week_drops.append({
                    'subwave': sw_name,
                    'serial': d.get('serial_no'),
                    'author': d.get('author', {}).get('handle', ''),
                    'content': content[:300],
                    'created_at': dt.strftime('%Y-%m-%d %H:%M')
                })
    if week_drops:
        print(f"\n  Subwave: {sw_name} ({len(week_drops)} drops this week)")
        for d in week_drops[:10]:
            print(f"    {d['created_at']} @{d['author']}: {d['content'][:150]}")
        dev_drops_week.extend(week_drops)

print(f"\nTotal dev drops this week: {len(dev_drops_week)}")
print()

# 4. Museum wave drops
print("=== MUSEUM WAVE ===")
museum_wave = '5f207393-5418-4a75-8738-e40edb44a94d'
museum_drops = fetch(f'{API}/api/v2/waves/{museum_wave}/drops?limit=200')
m_drops = museum_drops.get('drops', [])
week_museum = []
for d in m_drops:
    ts = d.get('created_at', 0)
    if isinstance(ts, (int, float)) and ts > 1000000000:
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
        if week_start <= dt < week_end:
            content = d.get('content', '')
            if not content and d.get('parts'):
                content = d['parts'][0].get('content', '')
            week_museum.append({
                'serial': d.get('serial_no'),
                'author': d.get('author', {}).get('handle', ''),
                'content': content[:500],
                'drop_type': d.get('drop_type', ''),
                'created_at': dt.strftime('%Y-%m-%d %H:%M')
            })
print(f"Museum drops this week: {len(week_museum)}")
for d in week_museum[:20]:
    print(f"  {d['created_at']} @{d['author']} [{d['drop_type']}]: {d['content'][:200]}")
print()

# 5. MS Wave for winner posts
print("=== MS WAVE (WINNER drops) ===")
ms_wave = 'b6128077-ea78-4dd9-b381-52c4eadb2077'
ms_drops = fetch(f'{API}/api/waves/{ms_wave}/drops?limit=50&drop_type=WINNER')
ms_w = ms_drops.get('drops', [])
for d in ms_w:
    ts = d.get('created_at', 0)
    if isinstance(ts, (int, float)) and ts > 1000000000:
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
        content = d.get('content', '')
        if not content and d.get('parts'):
            content = d['parts'][0].get('content', '')
        if week_start <= dt < week_end:
            print(f"  WINNER {dt.strftime('%Y-%m-%d')} @{d.get('author', {}).get('handle', '')}: {content[:300]}")
        else:
            print(f"  (older) {dt.strftime('%Y-%m-%d')} @{d.get('author', {}).get('handle', '')}: {content[:200]}")
print()

# 6. Dive bar drops (sample for socials)
print("=== DIVE BAR (socials) ===")
dive_bar = 'b38288e6-ca9d-45ce-8323-3dc5e094f04e'
cursor = None
all_dive = []
batch_count = 0
cutoff_ms = int(week_start.timestamp() * 1000)
while batch_count < 500:
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
        if isinstance(ts, (int, float)) and ts >= cutoff_ms:
            content = d.get('content', '')
            if not content and d.get('parts'):
                content = d['parts'][0].get('content', '')
            all_dive.append({
                'serial': d.get('serial_no'),
                'author': d.get('author', {}).get('handle', ''),
                'content': content,
                'drop_type': d.get('drop_type', ''),
                'created_at': ts
            })
    cursor = drops[-1].get('serial_no', 0)
    batch_count += 1
    if oldest_ts < cutoff_ms:
        break
    time.sleep(0.3)

print(f"Total dive bar drops this week: {len(all_dive)}")
# Count unique authors
authors = set()
gm_count = 0
for d in all_dive:
    authors.add(d['author'])
    text = d['content'].lower().strip()
    if text.startswith('gm') or 'gmeme' in text or 'gm bar' in text or 'gm fam' in text:
        gm_count += 1
print(f"Unique authors: {len(authors)}")
print(f"GM count: {gm_count}")

# Save notable drops for analysis
notable_keywords = ['winner', 'congrats', 'welcome', 'card', 'vote', 'marfa', 'hack', 'drain',
                    'squiggle', 'pepe', 'marketplace', 'tdh', 'drama', 'debate', 'controversy',
                    'artblocks', 'art blocks', 'onboarding', 'cms', 'website', 'builder',
                    'citizen', 'death', 'taxes', 'pissarides', 'wine', 'vinetree', 'survive',
                    'conference', 'network state', 'physical', 'book', 'antifragile',
                    'clarify', 'clarified', 'mennens', 'blake', 'invoice', 'gas wars',
                    'carbon', 'hackathon', 'build', 'launch', 'release', 'deploy']
notable = []
for d in all_dive:
    text_lower = d['content'].lower()
    if any(kw in text_lower for kw in notable_keywords):
        notable.append(d)

print(f"\nNotable drops (keyword-matched): {len(notable)}")
# Sort by content length (longer = more substance usually)
notable.sort(key=lambda x: len(x['content']), reverse=True)
for d in notable[:40]:
    dt = datetime.fromtimestamp(d['created_at']/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d %H:%M')} @{d['author']} [{d['drop_type']}]: {d['content'][:250]}")
print()

# 7. Shillandia wave drops
print("=== SHILLANDIA WAVE ===")
shill_wave = '4bf2ed9a-7922-4e0f-9b57-c70b5e2fa4bd'
shill_data = fetch(f'{API}/api/v2/waves/{shill_wave}/drops?limit=200')
s_drops = shill_data.get('drops', [])
week_shill = []
for d in s_drops:
    ts = d.get('created_at', 0)
    if isinstance(ts, (int, float)) and ts > 1000000000:
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
        if week_start <= dt < week_end:
            content = d.get('content', '')
            if not content and d.get('parts'):
                content = d['parts'][0].get('content', '')
            week_shill.append({
                'serial': d.get('serial_no'),
                'author': d.get('author', {}).get('handle', ''),
                'content': content[:300],
                'created_at': dt.strftime('%Y-%m-%d %H:%M')
            })
print(f"Shillandia drops this week: {len(week_shill)}")
for d in week_shill[:15]:
    print(f"  {d['created_at']} @{d['author']}: {d['content'][:200]}")

# Save all data
output = {
    'week_num': week_num,
    'year': year,
    'week_start': week_start.isoformat(),
    'week_end': week_end.isoformat(),
    'dive_bar_count': len(all_dive),
    'dive_bar_authors': len(authors),
    'gm_count': gm_count,
    'dev_drops_count': len(dev_drops_week),
    'museum_drops_count': len(week_museum),
    'shillandia_drops_count': len(week_shill),
}
with open('/tmp/mnn_weekly_data.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n=== SUMMARY ===")
print(json.dumps(output, indent=2))