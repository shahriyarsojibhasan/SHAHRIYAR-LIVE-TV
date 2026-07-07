import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import random
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']

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
    base_url = channel['url'] # Clean URL only
    
    if not base_url.startswith('http'): return None
    if is_vod(base_url, channel['group']): return None
    
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': '*/*'}

    try:
        response = session.get(base_url, headers=headers, stream=True, timeout=(2.5, 4.0), verify=False)
        if response.status_code not in [200, 206]: return None
            
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type: return None
        
        chunk = next(response.iter_content(chunk_size=4096), None)
        if not chunk: return None
        
        text_chunk = chunk.decode('utf-8', errors='ignore')
        if '.m3u8' in base_url.lower() or 'mpegurl' in content_type:
            if '#EXTM3U' not in text_chunk or '#EXT-X-ENDLIST' in text_chunk: return None 
        elif '.mpd' in base_url.lower() or 'dash+xml' in content_type:
            if '<MPD' not in text_chunk and '<mpd' not in text_chunk: return None
            if 'type="static"' in text_chunk: return None 
            
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
    current = {}
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith('#EXTINF:'):
            current['logo'] = (re.search(r'tvg-logo="([^"]+)"', line) or [None, ""])[1]
            current['group'] = (re.search(r'group-title="([^"]+)"', line) or [None, "Uncategorized"])[1]
            current['name'] = line[line.find(',')+1:].strip() if ',' in line else "Unknown"
            
        elif line.startswith('http') and 'name' in current:
            clean_url = line.split('|')[0]
            current['url'] = clean_url
            
            search_str = f"{current['name']} {current['group']} {clean_url}".lower()
            if not any(kw in search_str for kw in blocked_keywords):
                playlist.append(current)
                
            current = {}
    return playlist

def combine_and_verify(playlist_sources, priority_order):
    raw_combined, seen = [], set()
    for source in [s for s in (priority_order + playlist_sources) if s]:
        for ch in read_raw_playlist(source):
            if ch['url'] not in seen:
                seen.add(ch['url'])
                raw_combined.append(ch)

    print(f"Total TV Channels (Clean): {len(raw_combined)}. Fast Verifying... 🚀")
    verified = []
    with requests.Session() as session:
        tasks = [(ch, session) for ch in raw_combined]
        with concurrent.futures.ThreadPoolExecutor(max_workers=250) as executor:
            for ch in executor.map(is_channel_live, tasks):
                if ch: 
                    ch['name'] = f"{ch['name']} | SHAHRIYAR LIVE TV"
                    verified.append(ch)
    return verified

def write_to_file(playlist, output_file, promo_channel=None):
    bd = datetime.now(timezone(timedelta(hours=6))).strftime('%Y-%m-%d %H:%M:%S')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"#EXTM3U\n# By SHAHRIYAR SOJIB HASAN\n# Update on {bd}\n\n")
        if promo_channel: 
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']))
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n" % (item['logo'], item['group'], item['name']))
            f.write(f"{item['url']}\n")

if __name__ == "__main__":
    priority = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    promo = {'logo': 'https://i.ibb.co.com/TFSssmW/image.png', 'channel_name': 'SHAHRIYAR LIVE TV', 'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'}
    
    final_list = combine_and_verify(sources, priority)
    write_to_file(final_list, 'SHAHRIYAR-LIVE-TV.m3u', promo)
    print(f"✅ Success! {len(final_list)} TV channels saved.")