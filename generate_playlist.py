import os
import requests
import re

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
        print("Error: Playlist source URL is None")
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
            with open(source, 'r', encoding='utf-8') as f: # Added encoding to prevent read errors
                content = f.read()
        except IOError as e:
            print(f"Error reading file {source}: {e}")
            return []

    pattern = re.compile(r'#EXTINF:(.*?)(?: tvg-logo="(.*?)")?(?: group-title="(.*?)")?,(.*?)\n(.*?)\n', re.DOTALL)
    matches = pattern.findall(content)
    
    for match in matches:
        duration, logo, group, channel_name, url = match
        
        # --- Filter out unwanted channels ---
        channel_name_lower = channel_name.strip().lower()
        
        # Check if "himel op" is in the channel name
        if 'himel op' in channel_name_lower:
            continue # Skip this channel
            
        # Check if it's a short promo (assuming promo is in the group or name)
        # You can adjust this logic based on how promos are usually named in your source
        if 'promo' in channel_name_lower or (group and 'promo' in group.strip().lower()):
            continue # Skip this channel
            
        if '.m3u8' in url and is_channel_live(url):
            playlist.append({'logo': logo, 'group': group, 'channel_name': channel_name.strip(), 'url': url.strip()})
    return playlist

def combine_playlists(playlist_sources, priority_order):
    combined_playlist = []
    seen_channels = set()

    # Filter out None values from the lists before combining
    valid_sources = [s for s in priority_order + playlist_sources if s is not None]

    for source in valid_sources:
        source_playlist = read_m3u_playlist(source)
        for channel in source_playlist:
            channel_identity = (channel['channel_name'].lower(), channel['url'])
            if channel_identity not in seen_channels:
                seen_channels.add(channel_identity)
                combined_playlist.append(channel)

    return combined_playlist

def write_to_file(playlist, output_file, include_credits=False, promo_channel=None):
    credit_text = "# All the links in this file are collected from public sources. If anyone wants to remove their source, please let us know. We respect your opinions and efforts, so we will not object to removing your source. https://www.t.me/shahriyartvbot\n"
    with open(output_file, 'w', encoding='utf-8') as f: # Added utf-8 encoding for write
        f.write("#EXTM3U\n")  
        if include_credits:
            f.write(credit_text)
            
        # Write YOUR promo channel first if provided
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
    playlist_sources = [
        os.getenv('PLAYLIST_SOURCE_URL_1'),
        os.getenv('PLAYLIST_SOURCE_URL_2'),
        os.getenv('PLAYLIST_SOURCE_URL_3')  
    ]
    priority_order = [
        os.getenv('PRIORITY_PLAYLIST_URL_1'),
        os.getenv('PRIORITY_PLAYLIST_URL_2'),
        os.getenv('PRIORITY_PLAYLIST_URL_3')  
    ]
    
    # 1. Output file name updated
    output_file = 'SHAHRIYAR-LIVE-TV.M3U8'
    include_credits = True  

    combined_playlist = combine_playlists(playlist_sources, priority_order)

    # ------------------------------------------------  Define promo channel ------------------------------------------------
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    write_to_file(combined_playlist, output_file, include_credits, promo_channel)

    print("Combined and filtered playlist written to", output_file)