import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 VLC/3.0.20'

DEFAULT_LEGAL_SOURCES = [
    'https://iptv-org.github.io/iptv/languages/ben.m3u',       # Bengali & BD FTA Channels
    'https://iptv-org.github.io/iptv/countries/bd.m3u',        # Bangladesh Official FTA
]

CURATED_GLOBAL_FTA = [
    {
        'name': 'Al Jazeera English HD',
        'group': '📰 NEWS',
        'logo': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Al_Jazeera_English_logo.svg/512px-Al_Jazeera_English_logo.svg.png',
        'url': 'https://live-hls-web-aje.getaj.net/AJE/03.m3u8'
    },
    {
        'name': 'DW English News HD',
        'group': '📰 NEWS',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/512px-Deutsche_Welle_symbol_2012.svg.png',
        'url': 'https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8'
    },
    {
        'name': 'France 24 English HD',
        'group': '📰 NEWS',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/France_24_logo.svg/512px-France_24_logo.svg.png',
        'url': 'https://static.france24.com/live/F24_EN_LO_HLS/live_tv.m3u8'
    },
    {
        'name': 'NASA TV Public HD',
        'group': '🌍 DOCUMENTARY',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/512px-NASA_logo.svg.png',
        'url': 'https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8'
    },
    {
        'name': 'Red Bull TV HD',
        'group': '⚽ SPORTS',
        'logo': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f5/Red_Bull_TV_logo.svg/512px-Red_Bull_TV_logo.svg.png',
        'url': 'https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8'
    }
]

BLOCKED_KEYWORDS = [
    'himel op', 'test', 'dummy', 'trailer', 'promo', 'offline', 'dead', 
    'adult', 'xxx', 'porn', '18+', 'vod', 'movie', 'series', 'unnamed'
]

def clean_channel_name(raw_name):
    name = re.sub(r'\s*\|\s*SHAHRIYAR LIVE TV.*$', '', raw_name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(\d+p\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    return name.strip()

def normalize_group(name, group=""):
    g = group.strip().lower()
    n = name.lower()
    
    if any(k in n or k in g for k in ['bangla', 'dhaka', 'boishakhi', 'ananda', 'jamuna', 'somoy', 'ekhon', 'dbc', 'deshi', 'atn', 'channel i', 'gaan', 'nagorik', 'bijoy', 'gazi', 'massranga', 'independent']):
        return "🇧🇩 BANGLADESH"
    if any(k in n or k in g for k in ['sport', 'cricket', 'football', 'fifa', 'racing', 'red bull', 'wwe']):
        return "⚽ SPORTS"
    if any(k in n or k in g for k in ['news', 'khabar', 'samachar', 'al jazeera', 'bbc', 'dw', 'france 24', 'reuters', 'cna', 'times', 'cnn']):
        return "📰 NEWS"
    if any(k in n or k in g for k in ['music', 'song', 'gaana', 'sangeet', 'mtv', 'b4u', 'zoom']):
        return "🎵 MUSIC"
    if any(k in n or k in g for k in ['kid', 'cartoon', 'anime', 'duronto', 'disney', 'pogo', 'nick']):
        return "👶 KIDS"
    if any(k in n or k in g for k in ['movie', 'cinema', 'drama', 'entertainment', 'natok', 'zee', 'sony', 'star', 'colors']):
        return "🎬 ENTERTAINMENT"
    if any(k in n or k in g for k in ['doc', 'science', 'nasa', 'nature', 'geo', 'discovery', 'history']):
        return "🌍 DOCUMENTARY"
    return "🌐 WORLD TV"

def is_vod(url, group=""):
    url_clean = url.lower().split('?')[0].split('|')[0]
    vod_exts = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm']
    if any(url_clean.endswith(ext) for ext in vod_exts): 
        return True
    if any(p in url_clean for p in ['/movie/', '/series/', '/vod/', '/movies/']): 
        return True
    return False

def get_headers_for_channel(channel):
    headers = {'User-Agent': USER_AGENT, 'Accept': '*/*'}
    if '|' in channel['url']:
        pipe_opts = channel['url'].split('|', 1)[1]
        for opt in ['User-Agent', 'Referer', 'Cookie']:
            m = re.search(fr'{opt}=([^&]+)', pipe_opts, re.IGNORECASE)
            if m: 
                headers[opt] = m.group(1).strip()
    for opt in channel.get('vlcopt', []):
        if 'http-user-agent=' in opt: 
            headers['User-Agent'] = opt.split('http-user-agent=')[1].strip()
    return headers

def verify_app_stream(args):
    channel, session = args
    base_url = channel['url'].split('|')[0].strip()
    
    if not base_url.startswith('http'): 
        return None
    if is_vod(base_url, channel['group']): 
        return None

    try:
        res = session.get(base_url, headers=get_headers_for_channel(channel), stream=True, timeout=(2.5, 3.5), verify=False)
        if res.status_code not in [200, 206, 403]:
            return None

        content_type = res.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type and res.status_code == 200:
            return None

        return channel
    except Exception:
        return None

def fetch_m3u_with_metadata(source_url, max_limit=150):
    if not source_url:
        return []
    try:
        if source_url.startswith('http'):
            text = requests.get(source_url, timeout=6, verify=False).text
        else:
            text = open(source_url, 'r', encoding='utf-8', errors='ignore').read()
    except Exception:
        return []

    channels = []
    lines = text.replace('\r\n', '\n').split('\n')
    current = {'vlcopt': [], 'exthttp': [], 'kodiprop': []}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('#EXTINF:'):
            logo_m = re.search(r'tvg-logo="([^"]+)"', line)
            group_m = re.search(r'group-title="([^"]+)"', line)
            name_idx = line.rfind(',')
            
            raw_name = line[name_idx+1:].strip() if name_idx != -1 else "Live TV"
            current['name'] = clean_channel_name(raw_name)
            current['logo'] = logo_m.group(1).strip() if logo_m else ""
            current['group'] = group_m.group(1).strip() if group_m else "General"

        elif line.startswith('#EXTVLCOPT:'):
            current['vlcopt'].append(line)
        elif line.startswith('#EXTHTTP:'):
            current['exthttp'].append(line)
        elif line.startswith('#KODIPROP:'):
            current['kodiprop'].append(line)
        elif line.startswith('http') and 'name' in current:
            current['url'] = line
            current['group'] = normalize_group(current['name'], current['group'])

            search_blob = f"{current['name']} {current['group']} {line}".lower()
            if not any(k in search_blob for k in BLOCKED_KEYWORDS):
                channels.append(current)
                if len(channels) >= max_limit:
                    break

            current = {'vlcopt': [], 'exthttp': [], 'kodiprop': []}

    return channels

def generate_app_playlist():
    env_priority = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    env_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    
    active_env_priority = [s for s in env_priority if s and s.strip()]
    active_env_sources = [s for s in env_sources if s and s.strip()]

    all_sources = active_env_priority + active_env_sources + DEFAULT_LEGAL_SOURCES

    print(f"📥 [APP] Loading sources: {len(active_env_priority)} priority, {len(active_env_sources)} regular, {len(DEFAULT_LEGAL_SOURCES)} legal defaults.", flush=True)

    raw_channels = []
    seen_urls = set()

    for item in CURATED_GLOBAL_FTA:
        ch = dict(item)
        ch['vlcopt'] = []
        ch['exthttp'] = []
        ch['kodiprop'] = []
        raw_channels.append(ch)
        seen_urls.add(ch['url'])

    for src in all_sources:
        for ch in fetch_m3u_with_metadata(src, max_limit=150):
            clean_url = ch['url'].split('|')[0].strip()
            if clean_url not in seen_urls:
                seen_urls.add(clean_url)
                raw_channels.append(ch)

    print(f"📡 [APP] Collected {len(raw_channels)} candidate channels. Verifying fast... 🚀", flush=True)

    verified = []
    with requests.Session() as session:
        tasks = [(ch, session) for ch in raw_channels]
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            for res in executor.map(verify_app_stream, tasks):
                if res:
                    verified.append(res)

    print(f"✅ [APP] Verified {len(verified)} playable streams.", flush=True)

    unique_channels = {}
    for ch in verified:
        key = ch['name'].lower()
        if key not in unique_channels:
            unique_channels[key] = ch

    final_list = list(unique_channels.values())

    category_order = {
        "🇧🇩 BANGLADESH": 1,
        "⚽ SPORTS": 2,
        "📰 NEWS": 3,
        "🎬 ENTERTAINMENT": 4,
        "🎵 MUSIC": 5,
        "👶 KIDS": 6,
        "🌍 DOCUMENTARY": 7,
        "🌐 WORLD TV": 8
    }

    final_list.sort(key=lambda c: (category_order.get(c['group'], 99), c['name']))

    if len(final_list) > 150:
        final_list = final_list[:150]

    now_bd = datetime.now(timezone(timedelta(hours=6))).strftime('%Y-%m-%d %H:%M:%S')
    output_file = 'SHAHRIYAR-LIVE-TV-APP.m3u'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("# SHAHRIYAR LIVE TV APP - For OTT Navigator, VLC & Android\n")
        f.write(f"# Updated on: {now_bd} (BDT)\n")
        f.write(f"# Total Playable Channels: {len(final_list)}\n\n")

        # Official Promo Channel
        f.write('#EXTINF:-1 tvg-logo="https://blogger.googleusercontent.com/img/a/AVvXsEjz0o_rUO-ESkNHIPrS97j51IBvyY35Z8GmEmmDOLQtRmErsvwvDka4XGmqpDlcDy6iNkfo3mc-ApousuAR4mrZoFlGYeBSO6HKxnlM62ODaMOAhOIAzXp34Q5pO39RV6UIKS-WjKFLh6tLB3KLHxqTivKYmRTdnZEmm9xUZw5tFeZ5YakHpd0jF3DU" group-title="🎬 PROMO",SHAHRIYAR LIVE TV Official\n')
        f.write('https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8\n\n')

        for ch in final_list:
            f.write(f'#EXTINF:-1 tvg-logo="{ch.get("logo", "")}" group-title="{ch["group"]}",{ch["name"]}\n')
            for vlc in ch.get('vlcopt', []):
                f.write(f"{vlc}\n")
            for exthttp in ch.get('exthttp', []):
                f.write(f"{exthttp}\n")
            for kodi in ch.get('kodiprop', []):
                f.write(f"{kodi}\n")
            f.write(f'{ch["url"]}\n')

    print(f"🎉 Successfully saved {len(final_list)} verified app channels to {output_file}!", flush=True)
    return len(final_list)

if __name__ == '__main__':
    generate_app_playlist()
