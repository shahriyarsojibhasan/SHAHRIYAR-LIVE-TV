import os
import requests
import re
from datetime import datetime, timezone, timedelta

def is_channel_live(url):
    try:
        response = requests.get(url, stream=True, timeout=5)
        # First check if the response is OK
        if response.status_code == 200:
            try:
                # Then try to read the first chunk of content
                next(response.iter_content(1024))
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
    playlist = []
    if source is None:
        return []

    if source.startswith("http"):
        try:
            response = requests.get(source)
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

    pattern = re.compile(r'#EXTINF:(.*?)(?: tvg-logo="(.*?)")?(?: group-title="(.*?)")?,(.*?)\n(.*?)\n', re.DOTALL)
    matches = pattern.findall(content)
    
    for match in matches:
        duration, logo, group, channel_name, url = match
        
        # --- Filter out unwanted channels ---
        channel_name_clean = channel_name.strip()
        channel_name_lower = channel_name_clean.lower()
        
        if 'himel op' in channel_name_lower:
            continue 
            
        if 'promo' in channel_name_lower or (group and 'promo' in group.strip().lower()):
            continue 
            
        if '.m3u8' in url and is_channel_live(url):
            # Add branding to channel name
            branded_channel_name = f"{channel_name_clean} | SHAHRIYAR LIVE TV"
            playlist.append({'logo': logo, 'group': group, 'channel_name': branded_channel_name, 'url': url.strip()})
            
    return playlist

def combine_playlists(playlist_sources, priority_order):
    combined_playlist = []
    seen_channels = set()

    # Filter out None values
    valid_sources = [s for s in priority_order + playlist_sources if s is not None]

    for source in valid_sources:
        source_playlist = read_m3u_playlist(source)
        for channel in source_playlist:
            # Check uniqueness based on the URL to avoid duplicates with different names
            channel_identity = channel['url']
            if channel_identity not in seen_channels:
                seen_channels.add(channel_identity)
                combined_playlist.append(channel)

    return combined_playlist

def write_to_file(playlist, output_file, promo_channel=None):
    # Calculate BD Time (UTC + 6 hours)
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write Custom Header
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIAYRTVBOT\n")
        f.write(f"# Update on {current_time_bd} (BD Time)\n")
        f.write("# Note: I do not host any content, everything is publicly available. And any issues, please contact me.\n\n")
            
        # Write promo channel first if provided
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
            
        # Write normal playlist channels
        for item in playlist:
            logo = item['logo'] if item['logo'] else ""
            group = item['group'] if item['group'] else ""
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (logo, group, item['channel_name'], item['url']))

if __name__ == "__main__":
    # Dynamically grab up to 20 normal sources and 10 priority sources from environment variables
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    
    # Updated output file extension to .m3u
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'

    combined_playlist = combine_playlists(playlist_sources, priority_order)

    # ------------------------------------------------  Define promo channel ------------------------------------------------
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    write_to_file(combined_playlist, output_file, promo_channel)

    print("Combined and filtered playlist written to", output_file)