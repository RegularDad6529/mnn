#!/usr/bin/env python3
"""Fetch card page data and additional info."""
import json, urllib.request, ssl, re, time
from datetime import datetime, timezone

with open('/home/prenode/.hermes/profiles/themanager/6529_tokens.json') as f:
    jwt = json.load(f)['token']

API = 'https://api.6529.io'
ssl_ctx = ssl.create_default_context()

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {jwt}',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            resp = urllib.request.urlopen(req, timeout=30, context=ssl_ctx)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return {'error': str(e)}
    return {}

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f'ERROR: {e}'

def get_card_page_data(card_id):
    html = fetch_html(f'https://6529.io/the-memes/{card_id}')
    if html.startswith('ERROR'):
        return {'error': html}
    
    # Find nftMeta
    idx = html.find('"nftMeta"')
    if idx < 0:
        idx = html.find('\\"nftMeta\\"')
    if idx < 0:
        return {'error': 'nftMeta not found'}
    
    chunk = html[idx:idx+3000]
    
    fields = {}
    for field in ['edition_size', 'museum_holdings', 'edition_size_cleaned', 'hodlers', 'burnt', 'created_at', 'supply']:
        match = re.search(r'\\"' + field + r'\\":\s*([^,}\\]+)', chunk)
        if not match:
            match = re.search(r'"' + field + r'":\s*([^,}]+)', chunk)
        if match:
            val = match.group(1).strip().strip('\\').strip('"')
            try:
                val = int(val)
            except:
                try:
                    val = float(val)
                except:
                    pass
            fields[field] = val
    
    # Also get artist and title
    name_match = re.search(r'\\"name\\":\\"([^"]+)\\"', chunk)
    if name_match:
        fields['name'] = name_match.group(1)
    
    return fields

# Cards to check - this week we have #553 (SummerMaxi), and also #552 if it exists
# From the NFT API output we saw cards but it was truncated. Let's check 551-555
print("=== CARD PAGE DATA ===")
for card_id in [551, 552, 553, 554, 555]:
    data = get_card_page_data(card_id)
    print(f"Card #{card_id}: {json.dumps(data)}")
    time.sleep(0.5)

# Also get NFT API data for specific cards
print("\n=== NFT API for specific cards ===")
for card_id in [551, 552, 553]:
    nft = fetch(f'{API}/api/nfts?collection=0x33FD426905F149f8376e227d0C9D3340AaD17aF1&limit=100&sort=recent')
    nfts = nft.get('data', [])
    for n in nfts:
        if n.get('id') == card_id:
            meta = n.get('metadata', {})
            attrs = {}
            if meta and 'attributes' in meta:
                for attr in meta['attributes']:
                    attrs[attr.get('trait_type', '')] = attr.get('value', '')
            print(f"  #{card_id}: name={n.get('name')} artist={n.get('artist')} supply={n.get('supply')} mint_price={n.get('mint_price')} issuance={attrs.get('Issuance Month','')}")
            break

# TDH endpoint for research holdings
CONTRACT = '0x33FD426905F149f8376e227d0C9D3340AaD17aF1'
print("\n=== RESEARCH WALLET HOLDINGS ===")
for card_id in [551, 552, 553]:
    tdh = fetch(f'{API}/api/tdh/nft/{CONTRACT}/{card_id}?page_size=25&sort=balance&sort_direction=DESC')
    holders = tdh.get('data', [])
    research_balance = 0
    for h in holders:
        if h.get('handle') == '6529Research':
            research_balance = h.get('balance', 0)
            break
    print(f"  Card #{card_id}: 6529Research holdings = {research_balance}")
    time.sleep(0.5)

# Subscriptions count
print("\n=== SUBSCRIPTION COUNTS ===")
for card_id in [551, 552, 553]:
    subs = fetch(f'{API}/api/subscriptions/memes/{card_id}/count?_={int(time.time())}')
    print(f"  Card #{card_id}: {subs}")
    time.sleep(0.5)

# Search for Shillandia wave
print("\n=== SEARCHING FOR SHILLANDIA WAVE ===")
waves = fetch(f'{API}/api/v2/waves?view=SEARCH&page=1&page_size=50')
all_waves = waves.get('data', [])
for w in all_waves:
    name = w.get('name', '').lower()
    if 'shill' in name or 'shillandia' in name:
        print(f"  Found: {w.get('name')} ID: {w.get('id')} drops: {w.get('metrics', {}).get('drops_count', 'N/A')}")

# Also check page 2
waves2 = fetch(f'{API}/api/v2/waves?view=SEARCH&page=2&page_size=50')
for w in waves2.get('data', []):
    name = w.get('name', '').lower()
    if 'shill' in name or 'shillandia' in name:
        print(f"  Found (p2): {w.get('name')} ID: {w.get('id')} drops: {w.get('metrics', {}).get('drops_count', 'N/A')}")

print("\n=== DEV TEAM EOD DETAILS ===")
dev_wave = '49f0e595-ec7c-4235-8695-a527f61b69f4'
subwaves_data = fetch(f'{API}/api/waves/{dev_wave}/subwaves')
subwaves = subwaves_data.get('data', [])
for sw in subwaves:
    if sw.get('name') == 'Dev Team Chat':
        drops = fetch(f'{API}/api/waves/{sw["id"]}/drops?limit=50')
        for d in drops.get('drops', []):
            ts = d.get('created_at', 0)
            if isinstance(ts, (int, float)) and ts > 1000000000:
                dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
                content = d.get('content', '')
                if not content and d.get('parts'):
                    content = d['parts'][0].get('content', '')
                author = d.get('author', {}).get('handle', '')
                # Only show EOD posts
                if 'EOD' in content or 'eod' in content.lower() or 'gm' in content.lower()[:10]:
                    print(f"\n  {dt.strftime('%Y-%m-%d %H:%M')} @{author}:")
                    print(f"  {content[:500]}")

print("\n=== MORE DIVE BAR NOTABLE CONTENT ===")
# Let me search the dive bar for specific themes
dive_bar = 'b38288e6-ca9d-45ce-8323-3dc5e094f04e'
week_start_ms = 1789948800000  # Sep 21 2026

cursor = None
controversies = []
ms_celebrations = []
art_topics = []
marfa_topics = []
pepe_topics = []
survive_topics = []
all_notable = []

# Get more drops with different keyword sets
extra_keywords = ['survive', 'exhibition', 'gallery', 'dominio', 'casa nua', 'casanua',
                  'wine', 'vinetree', 'patience', 'conference', 'network state',
                  'onboarding', 'new here', 'welcome', 'deploy', 'newsletter',
                  'gif', 'preview', 'static', 'manifold', 'superrare',
                  'pissarides', 'nobel', 'physical book', 'antifragile',
                  'bazaar', 'zar', 'cuttle', 'shill', 'allow list', 'allowlist',
                  'marfa', 'bar', 'drinks', 'blake', 'invoice',
                  'citizen', 'death and taxes', 'm0dest', 'phase 2',
                  'squiggle', 'chromie', 'art blocks']

batch_count = 0
while batch_count < 400:
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
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            text_lower = content.lower()
            
            # Check for extra keywords
            for kw in extra_keywords:
                if kw in text_lower:
                    all_notable.append({
                        'date': dt.strftime('%Y-%m-%d %H:%M'),
                        'author': author,
                        'content': content[:400],
                        'keyword': kw
                    })
                    break
    
    cursor = drops[-1].get('serial_no', 0)
    batch_count += 1
    if oldest_ts < week_start_ms:
        break
    time.sleep(0.3)

print(f"Extra notable drops: {len(all_notable)}")
# Group by keyword
from collections import Counter
kw_counts = Counter(d['keyword'] for d in all_notable)
print("Keyword distribution:", kw_counts.most_common(20))

# Print top items by keyword
for kw in ['survive', 'marfa', 'squiggle', 'wine', 'vinetree', 'patience', 'conference', 
           'onboarding', 'newsletter', 'gif', 'preview', 'static', 'physical book', 'antifragile',
           'citizen', 'death and taxes', 'blake', 'invoice', 'pissarides', 'nobel']:
    items = [d for d in all_notable if d['keyword'] == kw]
    if items:
        print(f"\n  --- {kw} ({len(items)} drops) ---")
        for item in items[:3]:
            print(f"  {item['date']} @{item['author']}: {item['content'][:250]}")

# Save for later
with open('/tmp/mnn_card_data.json', 'w') as f:
    json.dump({
        'cards': {str(cid): get_card_page_data(cid) for cid in [551, 552, 553]},
        'extra_notable': all_notable[:50]
    }, f, indent=2)