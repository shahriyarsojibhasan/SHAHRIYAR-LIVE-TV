import os
import requests
import re
import concurrent.futures
from datetime import datetime, timezone, timedelta

# Standard User-Agent to prevent 403 Forbidden errors from anti-bot systems
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*'
}

def is_channel_live(url):
    """
    Checks if a stream URL is playable by verifying its HTTP status,
    Content-Type, and attempting to read the first byte of data.
    """
    try:
        # 10-second timeout allows slower high-quality streams to respond
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        
        if response.status_code == 200:
            # Check Content-Type to ensure it's a media stream and not an HTML error page
            content_type = response.headers.get('Content-Type', '').lower()
            valid_media_types = ['video', 'audio', 'mpegurl', 'dash+xml', 'octet-stream']
            
            # If Content-Type is valid, try reading a chunk to confirm data flow
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
    Reads an M3U playlist from a URL or local file and parses its contents.
    """
    playlist = []
    if source is None:
        return []

    if source.startswith("http"):
        try:
            response = requests.get(source, headers=HEADERS, timeout=15)
            response.encoding = 'utf-8' # Force UTF-8 decoding
            content = response.text
        except requests.RequestException as e:
            print(f"Error fetching playlist from {source}: {e}")
            return []
    else:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading file {source}: {e}")
            return []

    # Normalize line endings to prevent regex mismatch across different OS/Servers
    content = content.replace('\r\n', '\n')

    # Regex to extract duration, logo, group, name, and URL
    pattern = re.compile(r'#EXTINF:(.*?)(?: tvg-logo="(.*?)")?(?: group-title="(.*?)")?,(.*?)\n(.*?)(?:\n|$)', re.DOTALL)
    matches = pattern.findall(content)
    
    # Blocklist for unwanted promotional or dummy channels
    blocked_keywords = ['himel op', 'promo', 'playz tv']
    
    for match in matches:
        duration, logo, group, channel_name, url = match
        
        channel_name_clean = channel_name.strip()
        channel_name_lower = channel_name_clean.lower()
        group_lower = group.strip().lower() if group else ""
        url_lower = url.strip().lower()
        
        # Skip channel if it contains any blocked keywords
        if any(kw in channel_name_lower or kw in group_lower or kw in url_lower for kw in blocked_keywords):
            continue 
            
        # Accept any valid HTTP/HTTPS streaming URL (M3U8, MPD, TS, MP4, etc.)
        if url_lower.startswith('http'):
            branded_channel_name = f"{channel_name_clean} | SHAHRIYAR LIVE TV"
            playlist.append({
                'logo': logo.strip() if logo else "", 
                'group': group.strip() if group else "Uncategorized", 
                'channel_name': branded_channel_name, 
                'url': url.strip()
            })
            
    return playlist

def check_channel_worker(channel):
    """Worker function for concurrent execution."""
    if is_channel_live(channel['url']):
        return channel
    return None

def combine_playlists(playlist_sources, priority_order):
    """
    Combines playlists, removes duplicates, and verifies stream status concurrently.
    """
    raw_combined_playlist = []
    seen_channels = set()

    # Filter out None or empty values
    valid_sources = [s for s in priority_order + playlist_sources if s]

    # 1. Collect all unique channels from the provided sources
    for source in valid_sources:
        source_playlist = read_m3u_playlist(source)
        for channel in source_playlist:
            channel_identity = channel['url']
            if channel_identity not in seen_channels:
                seen_channels.add(channel_identity)
                raw_combined_playlist.append(channel)

    combined_playlist = []
    print(f"Total channels extracted: {len(raw_combined_playlist)}. Verifying stream status with 20 threads... 🚀")

    # 2. Check stream status concurrently for maximum speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check_channel_worker, raw_combined_playlist)
        for channel in results:
            if channel is not None:
                combined_playlist.append(channel)

    return combined_playlist

def write_to_file(playlist, output_file, promo_channel=None):
    """
    Writes the final verified channels to an M3U file with custom headers.
    """
    # Calculate BD Time (UTC + 6 hours)
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write M3U Header and Metadata
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIAYRTVBOT\n")
        f.write(f"# Update on {current_time_bd} (BD Time)\n")
        f.write("# Note: I do not host any content, everything is publicly available. And any issues, please contact me.\n\n")
            
        # Inject Promo Channel at the top if provided
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
            
        # Write all playable channels
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (
                item['logo'], item['group'], item['channel_name'], item['url']
            ))

if __name__ == "__main__":
    # Dynamically fetch up to 20 normal sources and 10 priority sources from GitHub Secrets/ENV
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'

    combined_playlist = combine_playlists(playlist_sources, priority_order)

    # Define custom promotional channel to pin at the top
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    write_to_file(combined_playlist, output_file, promo_channel)
    
    print(f"Final valid playable channels: {len(combined_playlist)}")
    print(f"Combined and filtered playlist written successfully to {output_file}")