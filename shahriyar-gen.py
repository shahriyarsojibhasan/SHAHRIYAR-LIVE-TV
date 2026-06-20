import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta

# Standard User-Agent to prevent 403 Forbidden errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*'
}

def is_vod(url):
    """
    Checks if a URL is a VOD (Movie/Series) instead of a Live TV channel.
    IPTV panels usually use /movie/ or /series/ for VODs, and extensions like .mp4, .mkv.
    """
    url_lower = url.lower()
    
    # Common VOD file extensions
    vod_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov']
    if any(url_lower.endswith(ext) for ext in vod_extensions):
        return True
        
    # Common VOD paths in Xtream Codes API
    if '/movie/' in url_lower or '/series/' in url_lower:
        return True
        
    return False

def is_channel_live(url):
    """
    Checks if a stream URL is playable and responding.
    """
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            valid_media_types = ['video', 'audio', 'mpegurl', 'dash+xml', 'octet-stream']
            
            if any(media_type in content_type for media_type in valid_media_types) or not content_type:
                try:
                    next(response.iter_content(chunk_size=1024))
                    return True
                except StopIteration:
                    return False
        return False
    except requests.RequestException:
        return False
    finally:
        if 'response' in locals():
            response.close()

def read_m3u_playlist(source):
    """
    Bulletproof Line-by-Line M3U parser to guarantee 100% channel grabbing.
    """
    playlist = []
    if not source:
        return []

    content = ""
    if source.startswith("http"):
        try:
            response = requests.get(source, headers=HEADERS, timeout=15)
            response.encoding = 'utf-8'
            content = response.text
        except requests.RequestException as e:
            print(f"Error fetching playlist: {e}")
            return []
    else:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading file: {e}")
            return []

    # Normalize lines
    lines = content.replace('\r\n', '\n').split('\n')
    
    blocked_keywords = ['himel op', 'promo', 'playz tv']
    current_channel = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#EXTINF:'):
            # Extract Logo
            logo_start = line.find('tvg-logo="')
            if logo_start != -1:
                logo_end = line.find('"', logo_start + 10)
                current_channel['logo'] = line[logo_start + 10:logo_end]
            else:
                current_channel['logo'] = ""

            # Extract Group Title
            group_start = line.find('group-title="')
            if group_start != -1:
                group_end = line.find('"', group_start + 13)
                current_channel['group'] = line[group_start + 13:group_end]
            else:
                current_channel['group'] = "Uncategorized"

            # Extract Channel Name
            name_split = line.split(',')
            current_channel['name'] = name_split[-1].strip() if len(name_split) > 1 else "Unknown Channel"

        elif line.startswith('http'):
            if current_channel:
                url = line
                name_lower = current_channel['name'].lower()
                group_lower = current_channel['group'].lower()
                url_lower = url.lower()

                # 1. Block unwanted keywords
                if any(kw in name_lower or kw in group_lower or kw in url_lower for kw in blocked_keywords):
                    current_channel = {}
                    continue
                
                # 2. Block Movies & Series (VODs)
                if is_vod(url):
                    current_channel = {}
                    continue

                # 3. Apply Branding & Save
                branded_name = f"{current_channel['name']} | SHAHRIYAR LIVE TV"
                playlist.append({
                    'logo': current_channel['logo'],
                    'group': current_channel['group'],
                    'channel_name': branded_name,
                    'url': url
                })
                
                current_channel = {} # Reset for next channel

    return playlist

def check_channel_worker(channel):
    """Worker function for concurrent execution."""
    if is_channel_live(channel['url']):
        return channel
    return None

def combine_playlists(playlist_sources, priority_order):
    raw_combined_playlist = []
    seen_channels = set()

    valid_sources = [s for s in priority_order + playlist_sources if s]

    for source in valid_sources:
        source_playlist = read_m3u_playlist(source)
        for channel in source_playlist:
            channel_identity = channel['url']
            if channel_identity not in seen_channels:
                seen_channels.add(channel_identity)
                raw_combined_playlist.append(channel)

    combined_playlist = []
    print(f"Total Live TV channels extracted (Movies skipped): {len(raw_combined_playlist)}. Verifying stream status... 🚀")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check_channel_worker, raw_combined_playlist)
        for channel in results:
            if channel is not None:
                combined_playlist.append(channel)

    return combined_playlist

def write_to_file(playlist, output_file, promo_channel=None):
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIAYRTVBOT\n")
        f.write(f"# Update on {current_time_bd} (BD Time)\n")
        f.write("# Note: Auto-filtered to strictly contain Live TV only. No VODs/Movies.\n\n")
            
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
            
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (
                item['logo'], item['group'], item['channel_name'], item['url']
            ))

if __name__ == "__main__":
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'

    combined_playlist = combine_playlists(playlist_sources, priority_order)

    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    write_to_file(combined_playlist, output_file, promo_channel)
    
    print(f"Final valid Live TV channels: {len(combined_playlist)}")