import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import random
import urllib3
import re
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']

def get_headers(channel):
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': '*/*'}
    if '|' in channel['url']:
        pipe_opts = channel['url'].split('|', 1)[1]
        for opt in ['User-Agent', 'Referer', 'Cookie']:
            m = re.search(fr'{opt}=([^&]+)', pipe_opts, re.IGNORECASE)
            if m: headers[opt] = m.group(1).strip()
    for opt in channel.get('vlcopt', []):
        if 'http-user-agent=' in opt: headers['User-Agent'] = opt.split('http-user-agent=')[1].strip()
    for ext in channel.get('exthttp', []):
        try:
            cookie_data = json.loads(ext.replace('#EXTHTTP:', '').strip())
            if 'cookie' in cookie_data: headers['Cookie'] = cookie_data['cookie']
        except Exception: pass
    return headers

def is_vod(url, group=""):
    url_clean = url.lower().split('?')[0].split('|')[0]
    group_lower = group.lower()
    vod_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm']
    if any(url_clean.endswith(ext) for ext in vod_extensions): return True
    vod_patterns = ['/movie/', '/series/', '/vod/', '/movies/']
    if any(pattern in url_clean for pattern in vod_patterns): return True
    if 'vod' in group_lower.split() or group_lower == 'vods': return True
    return False

def is_channel_live(args):
    channel, session = args
    base_url = channel['url'].split('|')[0] if '|' in channel['url'] else channel['url']
    
    if not base_url.startswith('http'): return None
    if is_vod(base_url, channel['group']): return None
    
    try:
        response = session.get(base_url, headers=get_headers(channel), stream=True, timeout=(2.5, 4.0), verify=False)
        if response.status_code not in [200, 206, 403]: # 403 allowed for token DRM
            return None
        return channel
    except Exception: return None

def read_raw_playlist(source):
    playlist = []
    if not source: return []
    try:
        content = requests.get(source, timeout=10, verify=False).text if source.startswith("http") else open(source, 'r', encoding='utf-8').read()
    except Exception: return []

    lines = content.replace('\r\n', '\n').split('\n')
    blocked_keywords = ['himel op', 'promo', 'playz tv', 'test', 'dummy', 'vod', 'movies']
    current = {'vlcopt': [], 'exthttp': [], 'kodiprop': []}
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith('#EXTINF:'):
            current['logo'] = (re.search(r'tvg-logo="([^"]+)"', line) or [None, ""])[1]
            current['group'] = (re.search(r'group-title="([^"]+)"', line) or [None, "Uncategorized"])[1]
            current['name'] = line[line.find(',')+1:].strip() if ',' in line else "Unknown"
        elif line.startswith('#EXTVLCOPT:'): current['vlcopt'].append(line)
        elif line.startswith('#EXTHTTP:'): current['exthttp'].append(line)
        elif line.startswith('#KODIPROP:'): current['kodiprop'].append(line)
        elif line.startswith('http') and 'name' in current:
            current['url'] = line
            
            search_str = f"{current['name']} {current['group']} {line}".lower()
            if not any(kw in search_str for kw in blocked_keywords):
                playlist.append(current)
                
            current = {'vlcopt': [], 'exthttp': [], 'kodiprop': []}
    return playlist

def combine_and_sort(playlist_sources, priority_order):
    raw_combined, seen = [], set()
    for source in [s for s in (priority_order + playlist_sources) if s]:
        for ch in read_raw_playlist(source):
            if ch['url'] not in seen:
                seen.add(ch['url'])
                raw_combined.append(ch)

    print(f"Total App Channels (With Metadata): {len(raw_combined)}. Fast Verifying... 🚀")
    verified = []
    
    with requests.Session() as session:
        tasks = [(ch, session) for ch in raw_combined]
        with concurrent.futures.ThreadPoolExecutor(max_workers=250) as executor:
            for ch in executor.map(is_channel_live, tasks):
                if ch: 
                    ch['name'] = f"{ch['name']} | SHAHRIYAR LIVE TV"
                    verified.append(ch)

    # Custom Sorting Logic
    app_top_keywords = ['world cup', 'fifa', 'toffee', 't sports', 'tsports', 'bioscope']
    top_channels, rest_channels = [], []
    for ch in verified:
        if any(kw in (ch['name'] + " " + ch['group']).lower() for kw in app_top_keywords): top_channels.append(ch)
        else: rest_channels.append(ch)

    return top_channels + rest_channels

def write_to_file(playlist, output_file, promo_channel=None):
    bd = datetime.now(timezone(timedelta(hours=6))).strftime('%Y-%m-%d %H:%M:%S')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"#EXTM3U\n# By SHAHRIYAR SOJIB HASAN\n# Update on {bd}\n\n")
        if promo_channel: f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']))
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n" % (item['logo'], item['group'], item['name']))
            for vlc in item.get('vlcopt', []): f.write(f"{vlc}\n")
            for http in item.get('exthttp', []): f.write(f"{http}\n")
            for kodi in item.get('kodiprop', []): f.write(f"{kodi}\n")
            f.write(f"{item['url']}\n")

if __name__ == "__main__":
    priority = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    promo = {'logo': 'https://i.ibb.co.com/TFSssmW/image.png', 'channel_name': 'SHAHRIYAR LIVE TV', 'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'}
    
    final_list = combine_and_sort(sources, priority)
    write_to_file(final_list, 'SHAHRIYAR-LIVE-TV-APP.m3u', promo)
    print(f"✅ Success! {len(final_list)} App channels sorted and saved.")