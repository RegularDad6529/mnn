#!/usr/bin/env python3
"""Verify shillandia.html tab counts, div balance, and duplicates."""
import re, sys
from collections import Counter

with open("/home/prenode/mnn/shillandia.html") as f:
    html = f.read()

errors = []
fixes = []

# Tab sections and their IDs
TABS = [
    ('editions', 'Editions'),
    ('oneofone', '1/1s'),
    ('collections', 'Collections'),
    ('upcoming', 'Upcoming'),
    ('sold', 'Sold Out'),
]

# 1. Count actual drop-cards in each tab section
print("=== TAB COUNT VERIFICATION ===")
total_cards = 0
for tab_id, tab_name in TABS:
    # Find the section content
    # Pattern: id="tab_id" ... to the next tab section or end
    start_marker = f'id="{tab_id}"'
    start_idx = html.find(start_marker)
    if start_idx == -1:
        print(f"  {tab_name}: TAB SECTION NOT FOUND")
        errors.append(f"Tab section '{tab_id}' not found")
        continue
    
    # Find the end - next tab section or closing
    end_idx = len(html)
    for other_id, _ in TABS:
        if other_id == tab_id:
            continue
        other_marker = f'id="{other_id}"'
        other_idx = html.find(other_marker, start_idx + 1)
        if other_idx != -1 and other_idx < end_idx:
            end_idx = other_idx
    
    section_html = html[start_idx:end_idx]
    
    # Count drop-cards in this section
    cards = re.findall(r'class="drop-card\s+(\w+)"', section_html)
    actual_count = len(cards)
    total_cards += actual_count
    
    # Find the declared count in the tab button
    count_pattern = rf"showTab\('{tab_id}'\)\">{re.escape(tab_name)}\s*<span class=\"tab-count\">(\d+)</span>"
    count_match = re.search(count_pattern, html)
    declared_count = int(count_match.group(1)) if count_match else -1
    
    match = "✓" if actual_count == declared_count else "✗"
    print(f"  {match} {tab_name}: declared={declared_count}, actual={actual_count}")
    
    if actual_count != declared_count:
        errors.append(f"{tab_name}: declared {declared_count} vs actual {actual_count}")
        fixes.append(("tab_count", tab_id, tab_name, actual_count, declared_count))

print(f"\n  Total cards: {total_cards}")

# 2. Check subtitle total
print("\n=== SUBTITLE VERIFICATION ===")
subtitle_match = re.search(r'(\d+)\s*drops listed', html)
subtitle_total = int(subtitle_match.group(1)) if subtitle_match else -1
match = "✓" if subtitle_total == total_cards else "✗"
print(f"  {match} Subtitle: {subtitle_total} vs actual total: {total_cards}")
if subtitle_total != total_cards:
    errors.append(f"Subtitle: {subtitle_total} vs actual total: {total_cards}")
    fixes.append(("subtitle", total_cards))

# 3. Div balance check
print("\n=== DIV BALANCE CHECK ===")
for tab_id, tab_name in TABS:
    start_marker = f'id="{tab_id}"'
    start_idx = html.find(start_marker)
    if start_idx == -1:
        continue
    
    end_idx = len(html)
    for other_id, _ in TABS:
        if other_id == tab_id:
            continue
        other_idx = html.find(f'id="{other_id}"', start_idx + 1)
        if other_idx != -1 and other_idx < end_idx:
            end_idx = other_idx
    
    section_html = html[start_idx:end_idx]
    open_divs = len(re.findall(r'<div\b', section_html))
    close_divs = len(re.findall(r'</div>', section_html))
    match = "✓" if open_divs == close_divs else "✗"
    diff = open_divs - close_divs
    print(f"  {match} {tab_name}: <div>={open_divs}, </div>={close_divs}, diff={diff}")
    if open_divs != close_divs:
        errors.append(f"{tab_name} div imbalance: {open_divs} open vs {close_divs} close (diff={diff})")

# 4. Check for duplicate cards (same platform URL)
print("\n=== DUPLICATE URL CHECK ===")
urls = re.findall(r'class="drop-title"><a href="([^"]+)"', html)
url_counts = Counter(urls)
dups = {u: c for u, c in url_counts.items() if c > 1}
if dups:
    print(f"  ✗ Found {len(dups)} duplicate URLs:")
    for u, c in dups.items():
        print(f"    {c}x {u[:80]}")
        errors.append(f"Duplicate URL: {u}")
else:
    print(f"  ✓ No duplicate URLs found ({len(urls)} total)")

# Summary
print("\n=== SUMMARY ===")
if errors:
    print(f"  {len(errors)} issues found:")
    for e in errors:
        print(f"    - {e}")
else:
    print("  All checks passed ✓")

# Apply fixes if needed
if fixes:
    print("\n=== APPLYING FIXES ===")
    new_html = html
    
    for fix in fixes:
        if fix[0] == "tab_count":
            _, tab_id, tab_name, actual, declared = fix
            old = f'showTab(\'{tab_id}\')">{tab_name} <span class="tab-count">{declared}</span>'
            new = f'showTab(\'{tab_id}\')">{tab_name} <span class="tab-count">{actual}</span>'
            new_html = new_html.replace(old, new)
            print(f"  Fixed tab count: {tab_name} {declared} → {actual}")
        elif fix[0] == "subtitle":
            _, actual_total = fix
            old_match = re.search(r'(\d+)\s*drops listed', new_html)
            if old_match:
                old_text = old_match.group(0)
                new_text = f"{actual_total} drops listed"
                new_html = new_html.replace(old_text, new_text)
                print(f"  Fixed subtitle: → {actual_total} drops listed")
    
    # Write fixed HTML
    with open("/home/prenode/mnn/shillandia.html", "w") as f:
        f.write(new_html)
    print("  Fixed HTML written!")

sys.exit(1 if errors else 0)
