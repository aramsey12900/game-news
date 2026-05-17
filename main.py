import feedparser
import re
import json
import time
from datetime import datetime

# List of RSS feeds (video game news sources)
sources = [
    "https://www.eurogamer.net/?format=rss",
    "https://www.gematsu.com/feed",
    "https://www.vg247.com/feed",
    "https://nintendoeverything.com/feed/",
    "https://www.ign.com/articles.rss",
    "https://kotaku.com/rss",
    "https://www.pcgamer.com/rss/",
    "https://www.rockpapershotgun.com/feed",
    "https://www.polygon.com/rss/index.xml",
    "https://gamerant.com/feed/",
    "https://www.gameinformer.com/rss.xml",
    "https://toucharcade.com/feed/",
    "https://www.gamespot.com/feeds/mashup/",
    "https://www.destructoid.com/feed/",
    "https://www.gamesradar.com/rss/",
    "https://www.siliconera.com/feed/",
    "https://www.dualshockers.com/feed/",
    "https://www.nintendolife.com/feeds/latest",
    "https://www.pushsquare.com/feeds/latest",
    "https://www.purexbox.com/feeds/latest",
    "https://www.gamedeveloper.com/rss.xml",
    "https://www.theverge.com/games/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/gaming",
    "https://wccftech.com/feed/"
]

# Franchise keywords for trending detection
FRANCHISES = [
    ("Pokémon",        ["pokemon"]),
    ("Zelda",          ["zelda"]),
    ("Sonic",          ["sonic"]),
    ("Halo",           ["halo"]),
    ("Mario",          ["mario"]),
    ("Call of Duty",   ["call of duty"]),
    ("Minecraft",      ["minecraft"]),
    ("Fortnite",       ["fortnite"]),
    ("FIFA",           ["fifa", "ea sports fc"]),
    ("God of War",     ["god of war"]),
    ("Final Fantasy",  ["final fantasy"]),
    ("Bethesda",       ["elder scrolls", "skyrim", "starfield", "fallout", "bethesda"]),
    ("GTA",            ["grand theft auto", "gta", "rockstar"]),
    ("PlayStation",    ["playstation", "ps5", "sony"]),
    ("Xbox",           ["xbox", "microsoft"]),
    ("Nintendo Switch",["nintendo switch"]),
    ("PC / Steam",     ["steam", "valve"]),
    ("Elden Ring",     ["elden ring"]),
    ("Cyberpunk",      ["cyberpunk"]),
    ("Diablo",         ["diablo"]),
    ("Resident Evil",  ["resident evil"]),
    ("Assassin's Creed",["assassin"]),
]

def get_timestamp(entry):
    for attr in ('published_parsed', 'updated_parsed'):
        t = getattr(entry, attr, None)
        if t:
            try:
                return int(time.mktime(t))
            except Exception:
                pass
    return 0

def get_date(entry):
    ts = get_timestamp(entry)
    if ts:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%b %d, %Y · %H:%M")
    for attr in ('published', 'updated'):
        val = entry.get(attr, '')
        if val:
            return val[:22]
    return ''

def get_image(entry):
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if m.get('url') and m.get('type', '').startswith('image'):
                return m['url']
        if entry.media_content[0].get('url'):
            return entry.media_content[0]['url']
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href', enc.get('url', ''))
    content = entry.get('summary', '') or entry.get('content', [{}])[0].get('value', '')
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return ''

def clean_summary(text):
    text = re.sub(r'<[^>]+>', '', text)
    return text[:200]

# Fetch all articles
articles = []
source_names = []

for url in sources:
    feed = feedparser.parse(url)
    source_name = feed.feed.title if hasattr(feed.feed, 'title') else url
    if source_name not in source_names:
        source_names.append(source_name)
    for entry in feed.entries[:5]:
        full = re.sub(r'<[^>]+>', '', entry.get('summary', 'No summary'))
        ts = get_timestamp(entry)
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": full[:200],
            "full_summary": full,
            "source": source_name,
            "image": get_image(entry),
            "date": get_date(entry),
            "timestamp": ts
        })

# Sort by date descending (newest first)
articles.sort(key=lambda a: a["timestamp"], reverse=True)

# Compute trending — count mentions across all article titles + summaries
trending = []
for label, keywords in FRANCHISES:
    count = 0
    for a in articles:
        text = (a["title"] + " " + a["summary"]).lower()
        if any(k in text for k in keywords):
            count += 1
    if count > 0:
        trending.append((label, keywords[0], count))

trending.sort(key=lambda x: x[2], reverse=True)
top_trending = trending[:8]

# Build trending HTML
trending_html = ""
for label, keyword, count in top_trending:
    trending_html += f'<button class="trend-chip" data-keyword="{keyword}" onclick="trendClick(this)">{label} <span class="trend-count">{count}</span></button>\n'

# Build photo data for lightbox
photo_data_list = [
    {"index": i, "img": a["image"], "title": a["title"], "source": a["source"]}
    for i, a in enumerate(articles)
]
photo_data_json = json.dumps(photo_data_list)

# Build filter buttons
filter_buttons = ""
for name in source_names:
    slug = name.replace(" ", "-").replace(".", "").lower()
    filter_buttons += f'<button class="filter-btn active" data-source="{slug}" onclick="toggleSource(this)">{name}</button>\n'

# Build article cards
article_cards = ""
for i, a in enumerate(articles):
    slug = a["source"].replace(" ", "-").replace(".", "").lower()
    summary = a["summary"].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    title = a["title"].replace('<', '&lt;').replace('>', '&gt;')
    image_html = f'<img src="{a["image"]}" alt="" class="card-img" onclick="openLightbox({i})" onerror="this.style.display=\'none\'">' if a["image"] else ''
    date_html = f'<span class="date">🕒 {a["date"]}</span>' if a["date"] else ''
    full = a["full_summary"].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    article_cards += f"""
    <div class="news" data-source="{slug}" data-ts="{a['timestamp']}" data-url="{a['link']}">
        {image_html}
        <div class="news-body">
            <div class="title"><a href="{a['link']}" target="_blank">{title}</a><span class="new-badge" style="display:none">NEW</span></div>
            <div class="summary preview">{summary}...</div>
            <div class="summary full" style="display:none">{full}</div>
            <div class="meta">
                {date_html}
                <span class="source">📰 {a['source']}</span>
                <button class="bookmark-btn" title="Save for later" data-url="{a['link']}" data-title="{title}" data-source="{a['source']}" onclick="toggleBookmark(this)">🔖</button>
                <button class="expand-btn" onclick="toggleExpand(this)">▼ Read more</button>
            </div>
        </div>
    </div>"""

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Daily Game News</title>
    <meta charset="UTF-8">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{ font-family: Arial; margin: 0; padding: 0; background: #121212; color: #ffffff; }}
        .page-wrapper {{ display: flex; min-height: 100vh; }}

        /* Sidebar */
        .sidebar {{
            width: 220px;
            min-width: 220px;
            background: #1a1a1a;
            border-right: 1px solid #2a2a2a;
            padding: 16px 12px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease;
        }}
        .sidebar.hidden {{ width: 0; min-width: 0; padding: 0; overflow: hidden; }}
        .sidebar h3 {{ color: #90caf9; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px; white-space: nowrap; }}
        .sidebar-section {{ margin-bottom: 20px; }}
        .filter-btn {{
            display: block; width: 100%; text-align: left;
            padding: 6px 10px; border: none; background: transparent;
            color: #aaa; border-radius: 6px; cursor: pointer;
            font-size: 0.8em; transition: all 0.15s; margin-bottom: 2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }}
        .filter-btn:hover {{ background: #2a2a2a; color: #fff; }}
        .filter-btn.inactive {{ color: #444; }}
        .filter-btn.active {{ color: #fff; }}
        .toggle-all {{
            display: block; width: 100%; padding: 5px 10px;
            border: 1px solid #444; background: transparent; color: #888;
            border-radius: 6px; cursor: pointer; font-size: 0.76em;
            margin-bottom: 10px; text-align: left; white-space: nowrap;
        }}
        .toggle-all:hover {{ background: #2a2a2a; color: #fff; }}
        .franchise-btn {{
            display: block; width: 100%; text-align: left;
            padding: 6px 10px; border: none; background: transparent;
            color: #b39ddb; border-radius: 6px; cursor: pointer;
            font-size: 0.8em; transition: all 0.15s; margin-bottom: 2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }}
        .franchise-btn:hover {{ background: #2a2a3a; color: #d0b8f8; }}
        .franchise-btn.active {{ background: #3a2a5a; color: #d0b8f8; font-weight: bold; }}

        /* Main */
        .main-content {{ flex: 1; padding: 20px; max-width: 100%; overflow: hidden; min-width: 0; }}
        .header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }}
        .header-left {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
        h1 {{ margin: 0; font-size: 1.3em; color: #fff; }}
        .sidebar-toggle {{ background: #1e1e1e; border: 1px solid #333; color: #90caf9; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85em; white-space: nowrap; }}
        .sidebar-toggle:hover {{ background: #2a2a2a; }}
        .sort-toggle {{ background: #1e1e1e; border: 1px solid #333; color: #aaa; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85em; white-space: nowrap; }}
        .sort-toggle:hover {{ background: #2a2a2a; color: #fff; }}
        .sort-toggle.active {{ border-color: #90caf9; color: #90caf9; }}
        .countdown {{ font-size: 0.8em; color: #888; white-space: nowrap; }}

        /* Trending */
        .trending-bar {{
            display: flex; flex-wrap: wrap; gap: 8px;
            background: #1a1a1a; border: 1px solid #2a2a2a;
            padding: 12px 14px; border-radius: 8px; margin-bottom: 16px;
            align-items: center;
        }}
        .trending-label {{ font-size: 0.8em; color: #f39c12; font-weight: bold; margin-right: 4px; white-space: nowrap; }}
        .trend-chip {{
            padding: 4px 10px; background: #2a2a1a; border: 1px solid #f39c12;
            color: #f1c40f; border-radius: 20px; cursor: pointer; font-size: 0.78em;
            transition: all 0.2s; white-space: nowrap;
        }}
        .trend-chip:hover {{ background: #f39c12; color: #000; }}
        .trend-count {{ background: #f39c12; color: #000; border-radius: 10px; padding: 1px 6px; font-size: 0.85em; font-weight: bold; margin-left: 4px; }}

        /* Articles */
        #articles {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; width: 100%; }}
        .news {{ background: #1e1e1e; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.4); overflow: hidden; display: flex; flex-direction: column; }}
        .news.hidden {{ display: none; }}
        .news img {{ width: 100%; height: 180px; object-fit: cover; display: block; }}
        .news-body {{ padding: 15px; flex: 1; display: flex; flex-direction: column; }}
        .title {{ font-size: 1em; margin-bottom: 8px; line-height: 1.4; }}
        .title a {{ text-decoration: none; color: #90caf9; }}
        .title a:hover {{ color: #42a5f5; }}
        .summary {{ color: #ffffff; font-size: 0.85em; line-height: 1.5; }}
        .meta {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: auto; padding-top: 10px; }}
        .date {{ font-size: 0.75em; color: #888; }}
        .source {{ font-size: 0.75em; color: #666; }}
        .expand-btn {{ background: none; border: none; color: #90caf9; font-size: 0.75em; cursor: pointer; padding: 0; margin-left: auto; }}
        .expand-btn:hover {{ color: #42a5f5; }}
        .card-img {{ cursor: zoom-in; transition: opacity 0.2s; }}
        .card-img:hover {{ opacity: 0.85; }}
        .new-badge {{ background: #e74c3c; color: white; font-size: 0.65em; font-weight: bold; padding: 2px 7px; border-radius: 10px; letter-spacing: 0.5px; vertical-align: middle; margin-left: 6px; flex-shrink: 0; }}
        .search-wrap {{ position: relative; margin-bottom: 16px; }}
        .search-bar {{ width: 100%; padding: 10px 36px 10px 14px; background: #1e1e1e; border: 1px solid #333; border-radius: 8px; color: #fff; font-size: 0.9em; outline: none; transition: border-color 0.2s; }}
        .search-bar:focus {{ border-color: #90caf9; }}
        .search-bar::placeholder {{ color: #555; }}
        .search-clear {{ position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: #555; cursor: pointer; font-size: 1em; display: none; }}
        .search-clear:hover {{ color: #fff; }}
        .search-count {{ font-size: 0.75em; color: #888; margin-bottom: 10px; min-height: 1em; }}
        .theme-toggle {{ background: #1e1e1e; border: 1px solid #333; color: #aaa; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85em; white-space: nowrap; }}
        .theme-toggle:hover {{ background: #2a2a2a; color: #fff; }}

        /* Light mode */
        body.light {{ background: #f0f2f5; color: #1a1a1a; }}
        body.light .sidebar {{ background: #e4e7ec; border-right-color: #ccc; }}
        body.light .sidebar-label {{ color: #444; }}
        body.light .filter-btn {{ background: #d8dce4; color: #333; border-color: #bbb; }}
        body.light .filter-btn:hover {{ background: #c8cdd8; color: #000; }}
        body.light .filter-btn.inactive {{ color: #999; }}
        body.light .filter-btn.active {{ color: #1a1a1a; }}
        body.light .toggle-all {{ border-color: #bbb; color: #666; }}
        body.light .toggle-all:hover {{ background: #c8cdd8; color: #000; }}
        body.light .franchise-btn {{ color: #6a4ab0; }}
        body.light .franchise-btn:hover {{ background: #ddd6f0; color: #4a2a90; }}
        body.light .franchise-btn.active {{ background: #c9baea; color: #3a1a70; }}
        body.light h1 {{ color: #1a1a1a; }}
        body.light .sidebar-toggle, body.light .sort-toggle, body.light .theme-toggle {{ background: #d8dce4; border-color: #bbb; color: #333; }}
        body.light .sidebar-toggle:hover, body.light .sort-toggle:hover, body.light .theme-toggle:hover {{ background: #c8cdd8; color: #000; }}
        body.light .sort-toggle.active {{ border-color: #3a7ecf; color: #3a7ecf; }}
        body.light .countdown {{ color: #666; }}
        body.light .trending-bar {{ background: #e8e4d0; border-color: #d4c97a; }}
        body.light .trend-chip {{ background: #f5edd0; border-color: #c9a800; color: #7a5f00; }}
        body.light .trend-chip:hover {{ background: #c9a800; color: #fff; }}
        body.light .news {{ background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.12); }}
        body.light .title a {{ color: #1a5fa8; }}
        body.light .title a:hover {{ color: #0d3d7a; }}
        body.light .summary {{ color: #333; }}
        body.light .source-label {{ background: #e0e4ee; color: #444; }}
        body.light .date {{ color: #666; }}
        body.light .expand-btn {{ color: #1a5fa8; }}
        body.light .search-bar {{ background: #fff; border-color: #bbb; color: #1a1a1a; }}
        body.light .search-bar:focus {{ border-color: #3a7ecf; }}
        body.light .search-bar::placeholder {{ color: #999; }}
        body.light .search-count {{ color: #555; }}
        body.light .no-results {{ color: #555; }}
        body.light .saved-item {{ background: #e8e8e8; }}
        body.light .saved-item a {{ color: #1a5fa8; }}
        body.light .saved-empty {{ color: #888; }}
        .bookmark-btn {{ background: none; border: none; font-size: 1em; cursor: pointer; padding: 0; margin-left: 6px; opacity: 0.4; transition: opacity 0.2s, transform 0.15s; }}
        .bookmark-btn:hover {{ opacity: 1; transform: scale(1.2); }}
        .bookmark-btn.saved {{ opacity: 1; }}
        .saved-list {{ display: flex; flex-direction: column; gap: 6px; }}
        .saved-item {{ background: #222; border-radius: 6px; padding: 8px 10px; font-size: 0.78em; }}
        .saved-item a {{ color: #90caf9; text-decoration: none; display: block; margin-bottom: 4px; line-height: 1.4; }}
        .saved-item a:hover {{ color: #42a5f5; }}
        .saved-item-source {{ color: #555; font-size: 0.85em; }}
        .saved-item-remove {{ background: none; border: none; color: #555; cursor: pointer; font-size: 0.85em; float: right; padding: 0; }}
        .saved-item-remove:hover {{ color: #e74c3c; }}
        .saved-empty {{ color: #555; font-size: 0.8em; font-style: italic; }}
        #no-results {{ display: none; text-align: center; color: #666; padding: 40px; grid-column: span 2; }}
        hr {{ border: none; border-top: 1px solid #333; margin-top: 20px; }}
        p {{ color: #666; }}

        /* Lightbox */
        .lightbox {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 1000; align-items: center; justify-content: center; flex-direction: column; }}
        .lightbox.open {{ display: flex; }}
        .lightbox img {{ max-width: 90vw; max-height: 70vh; border-radius: 8px; object-fit: contain; }}
        .lightbox img.slide-in-right {{ animation: slideInRight 0.3s ease; }}
        .lightbox img.slide-in-left {{ animation: slideInLeft 0.3s ease; }}
        @keyframes slideInRight {{ from {{ transform: translateX(60px); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
        @keyframes slideInLeft {{ from {{ transform: translateX(-60px); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
        .lightbox-caption {{ color: #fff; margin-top: 16px; text-align: center; max-width: 80vw; font-size: 0.95em; }}
        .lightbox-caption .lb-source {{ color: #888; font-size: 0.8em; margin-top: 4px; }}
        .lightbox-nav {{ display: flex; align-items: center; gap: 24px; margin-top: 20px; }}
        .lightbox-nav button {{ background: #333; border: none; color: white; font-size: 1.5em; width: 48px; height: 48px; border-radius: 50%; cursor: pointer; transition: background 0.2s; }}
        .lightbox-nav button:hover {{ background: #555; }}
        .lightbox-close {{ position: fixed; top: 20px; right: 28px; background: none; border: none; color: #aaa; font-size: 2em; cursor: pointer; z-index: 1001; }}
        .lightbox-close:hover {{ color: white; }}
        .lightbox-counter {{ color: #888; font-size: 0.85em; }}
    </style>
</head>
<body>
<div class="page-wrapper">
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-section">
            <h3>🎮 Franchise</h3>
            <button class="franchise-btn active" data-keyword="" onclick="filterFranchise(this)">All</button>
            <button class="franchise-btn" data-keyword="pokemon" onclick="filterFranchise(this)">Pokémon</button>
            <button class="franchise-btn" data-keyword="zelda" onclick="filterFranchise(this)">Zelda</button>
            <button class="franchise-btn" data-keyword="sonic" onclick="filterFranchise(this)">Sonic</button>
            <button class="franchise-btn" data-keyword="halo" onclick="filterFranchise(this)">Halo</button>
            <button class="franchise-btn" data-keyword="mario" onclick="filterFranchise(this)">Mario</button>
            <button class="franchise-btn" data-keyword="call of duty" onclick="filterFranchise(this)">Call of Duty</button>
            <button class="franchise-btn" data-keyword="minecraft" onclick="filterFranchise(this)">Minecraft</button>
            <button class="franchise-btn" data-keyword="fortnite" onclick="filterFranchise(this)">Fortnite</button>
            <button class="franchise-btn" data-keyword="fifa|ea sports fc" onclick="filterFranchise(this)">FIFA</button>
            <button class="franchise-btn" data-keyword="god of war" onclick="filterFranchise(this)">God of War</button>
            <button class="franchise-btn" data-keyword="final fantasy" onclick="filterFranchise(this)">Final Fantasy</button>
            <button class="franchise-btn" data-keyword="elder scrolls|skyrim|starfield|fallout|bethesda" onclick="filterFranchise(this)">Bethesda</button>
            <button class="franchise-btn" data-keyword="grand theft auto|gta|rockstar" onclick="filterFranchise(this)">GTA</button>
            <button class="franchise-btn" data-keyword="playstation|ps5|sony" onclick="filterFranchise(this)">PlayStation</button>
            <button class="franchise-btn" data-keyword="xbox|microsoft" onclick="filterFranchise(this)">Xbox</button>
            <button class="franchise-btn" data-keyword="nintendo switch" onclick="filterFranchise(this)">Nintendo Switch</button>
            <button class="franchise-btn" data-keyword="pc|steam|valve" onclick="filterFranchise(this)">PC / Steam</button>
            <button class="franchise-btn" data-keyword="elden ring" onclick="filterFranchise(this)">Elden Ring</button>
            <button class="franchise-btn" data-keyword="cyberpunk" onclick="filterFranchise(this)">Cyberpunk</button>
            <button class="franchise-btn" data-keyword="diablo" onclick="filterFranchise(this)">Diablo</button>
            <button class="franchise-btn" data-keyword="resident evil" onclick="filterFranchise(this)">Resident Evil</button>
            <button class="franchise-btn" data-keyword="assassin" onclick="filterFranchise(this)">Assassin's Creed</button>
        </div>
        <div class="sidebar-section">
            <h3>📰 Sources</h3>
            <button class="toggle-all" onclick="toggleAll()">Toggle All</button>
            {filter_buttons}
        </div>
        <div class="sidebar-section">
            <h3>🔖 Saved</h3>
            <div class="saved-list" id="saved-list">
                <span class="saved-empty">Nothing saved yet.</span>
            </div>
        </div>
    </aside>

    <div class="main-content">
        <div class="header">
            <div class="header-left">
                <button class="sidebar-toggle" onclick="toggleSidebar()">☰ Filters</button>
                <h1>🎮 Game News – {datetime.now().strftime("%B %d, %Y")}</h1>
                <button class="sort-toggle active" id="sort-btn" onclick="toggleSort()">📅 Latest First</button>
                <button class="theme-toggle" id="theme-btn" onclick="toggleTheme()">☀️ Light Mode</button>
            </div>
            <span class="countdown" id="countdown">Next refresh in 30:00</span>
        </div>

        <div class="search-wrap">
            <input class="search-bar" id="search-bar" type="text" placeholder="🔍  Search articles..." oninput="onSearch(this.value)" />
            <button class="search-clear" id="search-clear" onclick="clearSearch()">✕</button>
        </div>
        <div class="search-count" id="search-count"></div>

        <div class="trending-bar">
            <span class="trending-label">🔥 Trending:</span>
            {trending_html}
        </div>

        <div id="articles">
            {article_cards}
        </div>
        <div id="no-results">No articles match. Try a different filter.</div>

        <div class="lightbox" id="lightbox" onclick="closeLightboxBg(event)">
            <button class="lightbox-close" onclick="closeLightbox()">✕</button>
            <img id="lb-img" src="" alt="">
            <div class="lightbox-caption">
                <div id="lb-title"></div>
                <div class="lb-source" id="lb-source"></div>
            </div>
            <div class="lightbox-nav">
                <button onclick="slidePhoto(-1)">&#8592;</button>
                <span class="lightbox-counter" id="lb-counter"></span>
                <button onclick="slidePhoto(1)">&#8594;</button>
            </div>
        </div>

        <hr>
        <p>Auto-updated every 30 min. {len(articles)} articles from {len(source_names)} sources.</p>
    </div>
</div>

<script>
    // --- Source toggle ---
    function toggleSource(btn) {{
        btn.classList.toggle('inactive');
        btn.classList.toggle('active');
        const source = btn.getAttribute('data-source');
        document.querySelectorAll(`.news[data-source="${{source}}"]`).forEach(el => el.classList.toggle('hidden'));
        checkEmpty();
    }}

    function toggleAll() {{
        const buttons = document.querySelectorAll('.filter-btn');
        const anyActive = [...buttons].some(b => b.classList.contains('active'));
        buttons.forEach(btn => {{
            btn.classList.toggle('active', !anyActive);
            btn.classList.toggle('inactive', anyActive);
            const source = btn.getAttribute('data-source');
            document.querySelectorAll(`.news[data-source="${{source}}"]`).forEach(el => el.classList.toggle('hidden', anyActive));
        }});
        checkEmpty();
    }}

    function checkEmpty() {{
        const visible = [...document.querySelectorAll('.news')].filter(c => !c.classList.contains('hidden') && c.style.display !== 'none').length;
        document.getElementById('no-results').style.display = visible === 0 ? 'block' : 'none';
    }}

    // --- Sort ---
    let sortedByDate = true;

    function toggleSort() {{
        const grid = document.getElementById('articles');
        const cards = [...grid.querySelectorAll('.news')];
        const btn = document.getElementById('sort-btn');

        if (sortedByDate) {{
            // Switch to by-source: restore original DOM order (by data-source grouping)
            cards.sort((a, b) => a.getAttribute('data-source').localeCompare(b.getAttribute('data-source')));
            btn.textContent = '📋 By Source';
            btn.classList.remove('active');
            sortedByDate = false;
        }} else {{
            // Switch to latest first
            cards.sort((a, b) => parseInt(b.getAttribute('data-ts')) - parseInt(a.getAttribute('data-ts')));
            btn.textContent = '📅 Latest First';
            btn.classList.add('active');
            sortedByDate = true;
        }}
        cards.forEach(c => grid.appendChild(c));
    }}

    // --- Sidebar ---
    function toggleSidebar() {{
        document.getElementById('sidebar').classList.toggle('hidden');
    }}

    // --- Countdown & refresh ---
    const INTERVAL = 30 * 60;
    let secondsLeft = INTERVAL;
    let countdownTimer;

    function formatTime(s) {{
        const m = Math.floor(s / 60).toString().padStart(2, '0');
        const sec = (s % 60).toString().padStart(2, '0');
        return `${{m}}:${{sec}}`;
    }}

    function startCountdown() {{
        clearInterval(countdownTimer);
        secondsLeft = INTERVAL;
        countdownTimer = setInterval(() => {{
            secondsLeft--;
            document.getElementById('countdown').textContent = `Next refresh in ${{formatTime(secondsLeft)}}`;
            if (secondsLeft <= 0) refreshNews();
        }}, 1000);
    }}

    function refreshNews() {{
        document.getElementById('countdown').textContent = 'Refreshing...';
        clearInterval(countdownTimer);
        fetch('/api/refresh', {{ method: 'POST' }})
            .then(r => r.json())
            .then(data => {{ if (data.success) location.reload(); else startCountdown(); }})
            .catch(() => startCountdown());
    }}

    startCountdown();

    // --- Lightbox ---
    const photoData = {photo_data_json};
    let currentPhoto = 0;

    function openLightbox(index) {{
        currentPhoto = index;
        showPhoto('slide-in-right');
        document.getElementById('lightbox').classList.add('open');
        document.addEventListener('keydown', handleKey);
    }}

    function closeLightbox() {{
        document.getElementById('lightbox').classList.remove('open');
        document.removeEventListener('keydown', handleKey);
    }}

    function closeLightboxBg(e) {{
        if (e.target === document.getElementById('lightbox')) closeLightbox();
    }}

    function handleKey(e) {{
        if (e.key === 'ArrowRight') slidePhoto(1);
        if (e.key === 'ArrowLeft') slidePhoto(-1);
        if (e.key === 'Escape') closeLightbox();
    }}

    function slidePhoto(dir) {{
        const imgs = photoData.filter(p => p.img);
        const currentIdx = imgs.findIndex(p => p.index === currentPhoto);
        const nextIdx = (currentIdx + dir + imgs.length) % imgs.length;
        currentPhoto = imgs[nextIdx].index;
        showPhoto(dir === 1 ? 'slide-in-right' : 'slide-in-left');
    }}

    function showPhoto(anim) {{
        const p = photoData[currentPhoto];
        const img = document.getElementById('lb-img');
        img.className = '';
        img.src = p.img;
        img.offsetWidth;
        img.classList.add(anim);
        document.getElementById('lb-title').textContent = p.title;
        document.getElementById('lb-source').textContent = '📰 ' + p.source;
        const imgs = photoData.filter(p => p.img);
        const pos = imgs.findIndex(p => p.index === currentPhoto) + 1;
        document.getElementById('lb-counter').textContent = pos + ' / ' + imgs.length;
    }}

    // --- Expand ---
    function toggleExpand(btn) {{
        const body = btn.closest('.news-body');
        const preview = body.querySelector('.summary.preview');
        const full = body.querySelector('.summary.full');
        const expanded = full.style.display !== 'none';
        preview.style.display = expanded ? '' : 'none';
        full.style.display = expanded ? 'none' : '';
        btn.textContent = expanded ? '▼ Read more' : '▲ Show less';
    }}

    // --- Franchise filter ---
    let activeFranchiseKeyword = '';

    function filterFranchise(btn) {{
        document.querySelectorAll('.franchise-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFranchiseKeyword = btn.getAttribute('data-keyword').toLowerCase();
        applyAllFilters();
    }}

    // --- Bookmarks ---
    function loadBookmarks() {{
        return JSON.parse(localStorage.getItem('gn_bookmarks') || '[]');
    }}

    function saveBookmarks(list) {{
        localStorage.setItem('gn_bookmarks', JSON.stringify(list));
    }}

    function toggleBookmark(btn) {{
        const url = btn.getAttribute('data-url');
        const title = btn.getAttribute('data-title');
        const source = btn.getAttribute('data-source');
        let list = loadBookmarks();
        const idx = list.findIndex(b => b.url === url);
        if (idx === -1) {{
            list.unshift({{ url, title, source }});
            btn.classList.add('saved');
            btn.title = 'Remove bookmark';
        }} else {{
            list.splice(idx, 1);
            btn.classList.remove('saved');
            btn.title = 'Save for later';
        }}
        saveBookmarks(list);
        renderSavedList();
    }}

    function removeBookmark(url) {{
        let list = loadBookmarks().filter(b => b.url !== url);
        saveBookmarks(list);
        document.querySelectorAll(`.bookmark-btn[data-url="${{CSS.escape(url)}}"]`).forEach(b => {{
            b.classList.remove('saved');
            b.title = 'Save for later';
        }});
        renderSavedList();
    }}

    function renderSavedList() {{
        const list = loadBookmarks();
        const container = document.getElementById('saved-list');
        if (list.length === 0) {{
            container.innerHTML = '<span class="saved-empty">Nothing saved yet.</span>';
            return;
        }}
        container.innerHTML = list.map(b => `
            <div class="saved-item">
                <button class="saved-item-remove" onclick="removeBookmark('${{b.url.replace(/'/g, "\\\\'")}}')" title="Remove">✕</button>
                <a href="${{b.url}}" target="_blank">${{b.title}}</a>
                <span class="saved-item-source">📰 ${{b.source}}</span>
            </div>
        `).join('');
    }}

    function initBookmarks() {{
        const saved = loadBookmarks();
        saved.forEach(b => {{
            document.querySelectorAll(`.bookmark-btn[data-url="${{CSS.escape(b.url)}}"]`).forEach(btn => {{
                btn.classList.add('saved');
                btn.title = 'Remove bookmark';
            }});
        }});
        renderSavedList();
    }}

    initBookmarks();

    // --- New since last visit ---
    function initNewBadges() {{
        const key = 'gn_seen_urls';
        const seenRaw = localStorage.getItem(key);
        const seen = seenRaw ? new Set(JSON.parse(seenRaw)) : null;
        const currentUrls = [];

        document.querySelectorAll('.news[data-url]').forEach(card => {{
            const url = card.getAttribute('data-url');
            currentUrls.push(url);
            if (seen !== null && !seen.has(url)) {{
                const badge = card.querySelector('.new-badge');
                if (badge) badge.style.display = 'inline';
            }}
        }});

        // Save current URLs as "seen" after a short delay
        setTimeout(() => {{
            localStorage.setItem(key, JSON.stringify(currentUrls));
        }}, 5000);
    }}

    initNewBadges();

    // --- Theme toggle ---
    function applyTheme(isLight) {{
        document.body.classList.toggle('light', isLight);
        const btn = document.getElementById('theme-btn');
        btn.textContent = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
    }}

    function toggleTheme() {{
        const isLight = !document.body.classList.contains('light');
        applyTheme(isLight);
        localStorage.setItem('gn_theme', isLight ? 'light' : 'dark');
    }}

    (function initTheme() {{
        const saved = localStorage.getItem('gn_theme');
        const preferLight = saved ? saved === 'light' : window.matchMedia('(prefers-color-scheme: light)').matches;
        applyTheme(preferLight);
    }})();

    // --- Search ---
    let searchQuery = '';

    function onSearch(val) {{
        searchQuery = val.trim().toLowerCase();
        document.getElementById('search-clear').style.display = searchQuery ? 'block' : 'none';
        applyAllFilters();
    }}

    function clearSearch() {{
        document.getElementById('search-bar').value = '';
        onSearch('');
    }}

    function applyAllFilters() {{
        const franchiseKeywords = activeFranchiseKeyword ? activeFranchiseKeyword.split('|') : [];
        let visible = 0;
        document.querySelectorAll('.news').forEach(card => {{
            if (card.classList.contains('hidden')) {{
                card.style.display = 'none';
                return;
            }}
            const text = card.innerText.toLowerCase();
            const franchiseOk = franchiseKeywords.length === 0 || franchiseKeywords.some(k => text.includes(k.trim()));
            const searchOk = !searchQuery || text.includes(searchQuery);
            const show = franchiseOk && searchOk;
            card.style.display = show ? '' : 'none';
            if (show) visible++;
        }});
        const countEl = document.getElementById('search-count');
        if (searchQuery) {{
            countEl.textContent = `${{visible}} article${{visible !== 1 ? 's' : ''}} matching "${{searchQuery}}"`;
        }} else {{
            countEl.textContent = '';
        }}
        document.getElementById('no-results').style.display = visible === 0 ? 'block' : 'none';
    }}

    // --- Trending chips ---
    function trendClick(chip) {{
        const keyword = chip.getAttribute('data-keyword');
        const btn = [...document.querySelectorAll('.franchise-btn')].find(b => b.getAttribute('data-keyword').startsWith(keyword));
        if (btn) {{ filterFranchise(btn); }}
        else {{
            activeFranchiseKeyword = keyword;
            document.querySelectorAll('.franchise-btn').forEach(b => b.classList.remove('active'));
            applyFranchiseFilter();
        }}
    }}
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ News page created: index.html ({len(articles)} articles from {len(source_names)} sources)")
print(f"🔥 Top trending: {', '.join(t[0] for t in top_trending)}")

