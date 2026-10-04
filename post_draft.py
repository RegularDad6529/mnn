#!/usr/bin/env python3
"""Post draft MNN weekly summary to the MNN wave - NO tags, NO mentioned_users."""
import json, urllib.request, ssl

with open('/home/prenode/.hermes/profiles/themanager/6529_tokens.json') as f:
    jwt = json.load(f)['token']

API = 'https://api.6529.io'
WAVE_ID = 'e3511305-e6e1-4efb-a3e0-81f250cadf7f'
REPORT_URL = 'https://regulardad6529.github.io/mnn/reports/2026-W39.html'

content = f"""MNN Issue #4 (W39) is live: {REPORT_URL}

CasaNUA's SURVIVE exhibition hit #1 on the Main Stage leaderboard with 53.9M TDH. SummerMaxi won MS with "Network State Conference 2026" (card #553, sold out in 48h), and smpsmyth won MS with "Patience is a Vinetree" (card pending). The Rare Pepe acquisition wave opened with DarrenSRS proposing GOXPEPE at 0.25 ETH. Antifragile Bazaar physical books are shipping.

On the dev side, 100 PRs merged. simo6529's Release Coordinator went live after weeks of sandbox testing. GelatoGenesis shipped a production newsletter and retired the eligibility materialisation infrastructure. prxt6529 fixed NFT previews and Manifold/SuperRare metadata resolution. ragnep improved mobile image handling and ReMeme submission artwork access.

The community faced painful wallet drains from old Magic Eden contract approvals. @pete, @AshtonTekno, and @MadaCollects reported losses. @sheltronica traced the cause to unrevoked approvals, not bad links. A deep conversation about whether this space has meaningfully changed lives drew honest responses from @Soliiiart, @maybe, and @SummerMaxi.

3,367 dive bar drops, 189 voices, 502 GMs this week. Full report at the link above."""

body = json.dumps({
    "wave_id": WAVE_ID,
    "drop_type": "CHAT",
    "parts": [{"content": content}]
}).encode('utf-8')

req = urllib.request.Request(
    f'{API}/api/drops',
    data=body,
    headers={
        'Authorization': f'Bearer {jwt}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    },
    method='POST'
)

ctx = ssl.create_default_context()
try:
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read().decode('utf-8'))
    print(f"Posted successfully! Drop ID: {result.get('id')}, Serial: {result.get('serial_no')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")