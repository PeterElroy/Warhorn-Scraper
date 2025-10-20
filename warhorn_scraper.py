
import requests
import feedparser
from datetime import date, datetime, timezone
from collections import defaultdict

FEED_URL = "https://warhorn.net/events/rpg-night-utrecht/schedule/Sef-unkZyzF-7vzRibjR.atom"

def fetch_feed(url):
    response = requests.get(url)
    response.raise_for_status()
    return feedparser.parse(response.content)

def parse_entry(entry):
    import re
    # Extract date from summary if present
    import re
    from html import unescape
    # Use content field for HTML info
    content = entry.get('content', [{}])[0].get('value', '')
    summary = entry.get('summary', '')
    date = None
    location = None
    dm_limit = None
    player_limit = None
    dm_signed_in = None
    player_signed_in = None
    # Look for date pattern like 'Wed 15/10' in content or summary
    date_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2})/(\d{1,2})', content or summary)
    if date_match:
        day = int(date_match.group(2))
        month = int(date_match.group(3))
        year = datetime.now().year
        if month < datetime.now().month:
            year += 1
        try:
            date = datetime(year, month, day)
        except Exception:
            date = None
    else:
        date_str = entry.get('published', entry.get('updated', ''))
        if date_str:
            try:
                date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            except Exception:
                date = None
    # Extract GM and player sign-in info from HTML content
    if content:
        html = unescape(content)
        gm_match = re.search(r'(\d+)/(\d+)\s*GM', html)
        player_match = re.search(r'(\d+)/(\d+)\s*players', html)
        if gm_match:
            dm_signed_in = int(gm_match.group(1))
            dm_limit = int(gm_match.group(2))
        if player_match:
            player_signed_in = int(player_match.group(1))
            player_limit = int(player_match.group(2))
    # Extract location from gd:where if available
    # Extract location from gd_where valueString if available
    if entry.get('gd_where') and entry['gd_where'].get('valueString'):
        location_str = entry['gd_where']['valueString']
        location = location_str.split(',')[0].strip().strip('"')
    # Fallback: extract location from HTML content if not found
    if not location and content:
        html = unescape(content)
        loc_match = re.search(r'at\s+([^<,]+)', html)
        if loc_match:
            location = loc_match.group(1).strip()
    # Title should be the text from the <title> field in the RSS entry, not from HTML content
    title = entry.get('title', '')
    if isinstance(title, dict) and 'value' in title:
        title = title['value']
    return {
        'date': date,
        'location': location,
        'dm_limit': dm_limit,
        'player_limit': player_limit,
        'dm_signed_in': dm_signed_in,
        'player_signed_in': player_signed_in,
        'title': title.strip(),
        'open_seats':player_limit-player_signed_in,
    }

def main():
    feed = fetch_feed(FEED_URL)
    today = datetime.now(timezone.utc).date()
    entries_by_date = defaultdict(list)
    for entry in feed.entries:
        info = parse_entry(entry)
        if info['date']:
            entries_by_date[info['date'].date()].append(info)
    # Find first date with entries, including today
    sorted_dates = sorted(entries_by_date.keys())
    first_date = None
    for d in sorted_dates:
        if d >= today:
            first_date = d
            break
    if not first_date:
        print("No entries for today or future dates.")
        return
    
    # Format first_date as 'dd Month' with full month name
    first_date_readable = first_date.strftime('%A %d %B')
    print(f"# RPG Night Utrecht - {first_date_readable}")
    print(f"## Great games with open seats for @everyone:")
    # Group entries by location
    import re
    grouped = defaultdict(list)
    for entry in entries_by_date[first_date]:
        if entry.get('open_seats', 0) == 0:
            continue
        location = entry['location'] or ""
        if location.startswith("Subcultures @"):
            location = location[len("Subcultures @"):].strip()
        grouped[location].append(entry)

    for location in sorted(grouped.keys()):
        print()
        print(f"__**=== {location} ===**__")
        for entry in grouped[location]:
            title = re.sub(r"\[[^\]]*\]|\([^\)]*\)|\{[^\}]*\}", "", entry['title']).strip()
            if entry['open_seats'] == 1:
                print(f"* **{title}** - {entry['open_seats']} seat left")
            else:
                print(f"* **{title}** - {entry['open_seats']} seats left")
if __name__ == "__main__":
    main()
    print()
print(f"Grab a seat: https://warhorn.net/events/rpg-night-utrecht/schedule/agenda")