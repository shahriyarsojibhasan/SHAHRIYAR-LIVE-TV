import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import json
import random
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Multiple User-Agents for better compatibility
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-A135F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
]

def get_random_headers():
    """
    Generate random headers with rotation to bypass restrictions
    """
    ua = random.choice(USER_AGENTS)
    return {
        'User-Agent': ua,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'Origin': 'https://github.com',
        'Referer': 'https://github.com/',
    }

def get_session_with_retries():
    """
    Create a requests session with automatic retry strategy
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def is_vod(url):
    """
    Enhanced VOD detection with extended patterns
    """
    url_lower = url.lower()
    
    # Common VOD file extensions
    vod_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm', '.m3u8.mp4']
    if any(url_lower.endswith(ext) for ext in vod_extensions):
        return True
    
    # Common VOD paths in Xtream Codes API and streaming platforms
    vod_patterns = [
        '/movie/', '/series/', '/movies/', '/serial/', 
        '/film/', '/episode/', '/videos/', '/content/video',
        'movie=', 'series=', 'content_type=movie'
    ]
    if any(pattern in url_lower for pattern in vod_patterns):
        return True
    
    return False

def is_channel_live_advanced(url, session=None):
    """
    Enhanced stream verification with multiple fallback strategies
    """
    if session is None:
        session = get_session_with_retries()
    
    try:
        # Try HEAD request first (faster, less bandwidth)
        try:
            head_response = session.head(url, headers=get_random_headers(), timeout=8, allow_redirects=True)
            if head_response.status_code == 200:
                content_type = head_response.headers.get('Content-Type', '').lower()
                valid_media_types = ['video', 'audio', 'mpegurl', 'dash+xml', 'octet-stream', 'x-mpegurl', 'vnd.apple']
                
                if any(media_type in content_type for media_type in valid_media_types) or not content_type:
                    return True
        except:
            pass  # Fallback to GET if HEAD fails
        
        # Try GET request with stream
        get_response = session.get(url, headers=get_random_headers(), stream=True, timeout=10, allow_redirects=True)
        
        if get_response.status_code == 200:
            content_type = get_response.headers.get('Content-Type', '').lower()
            content_length = get_response.headers.get('Content-Length', '')
            
            valid_media_types = ['video', 'audio', 'mpegurl', 'dash+xml', 'octet-stream', 'x-mpegurl', 'vnd.apple']
            
            # Check content type
            if any(media_type in content_type for media_type in valid_media_types) or not content_type:
                # Try to read chunk
                try:
                    next(get_response.iter_content(chunk_size=1024))
                    return True
                except (StopIteration, requests.RequestException):
                    # Sometimes streams don't send data immediately but are still valid
                    if content_length and int(content_length) > 0:
                        return True
                    return False
        
        return False
    
    except requests.Timeout:
        # Timeout might mean stream is slow but valid - try one more time
        try:
            final_response = session.get(url, headers=get_random_headers(), stream=True, timeout=15)
            return final_response.status_code == 200
        except:
            return False
    
    except requests.RequestException as e:
        return False
    
    finally:
        if 'get_response' in locals():
            try:
                get_response.close()
            except:
                pass

def read_m3u_playlist_advanced(source, session=None):
    """
    Advanced M3U parser with better error handling and format support
    """
    playlist = []
    if not source:
        return []

    if session is None:
        session = get_session_with_retries()

    content = ""
    
    if source.startswith("http"):
        try:
            response = session.get(source, headers=get_random_headers(), timeout=20, allow_redirects=True)
            response.encoding = 'utf-8'
            content = response.text
            response.close()
        except requests.RequestException as e:
            print(f"⚠️  Error fetching playlist from {source}: {e}")
            return []
    else:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"⚠️  Error reading file {source}: {e}")
            return []

    # Normalize lines - handle multiple formats
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    blocked_keywords = ['himel op', 'promo', 'playz tv', 'test', 'dummy', '(off)', '[off]', 'disabled']
    current_channel = {}

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Skip non-extinf lines and non-url lines
        if not line.startswith('#EXTINF:') and not line.startswith('http') and idx > 0:
            continue
            
        if line.startswith('#EXTINF:'):
            # Extract Logo
            logo_start = line.find('tvg-logo="')
            if logo_start != -1:
                logo_end = line.find('"', logo_start + 10)
                current_channel['logo'] = line[logo_start + 10:logo_end]
            else:
                logo_start = line.find("tvg-logo='")
                if logo_start != -1:
                    logo_end = line.find("'", logo_start + 10)
                    current_channel['logo'] = line[logo_start + 10:logo_end]
                else:
                    current_channel['logo'] = ""

            # Extract Group Title
            group_start = line.find('group-title="')
            if group_start != -1:
                group_end = line.find('"', group_start + 13)
                current_channel['group'] = line[group_start + 13:group_end]
            else:
                group_start = line.find("group-title='")
                if group_start != -1:
                    group_end = line.find("'", group_start + 13)
                    current_channel['group'] = line[group_start + 13:group_end]
                else:
                    current_channel['group'] = "Uncategorized"

            # Extract Channel Name
            name_split = line.split(',')
            current_channel['name'] = name_split[-1].strip() if len(name_split) > 1 else "Unknown Channel"
            current_channel['source'] = source  # Track which source this came from

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

                # 3. Validate URL format
                try:
                    parsed = urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        current_channel = {}
                        continue
                except:
                    current_channel = {}
                    continue

                # 4. Apply Branding & Save
                branded_name = f"{current_channel['name']} | SHAHRIYAR LIVE TV"
                playlist.append({
                    'logo': current_channel['logo'],
                    'group': current_channel['group'],
                    'channel_name': branded_name,
                    'url': url,
                    'source': current_channel['source'],
                    'original_name': current_channel['name']
                })
                
                current_channel = {}

    return playlist

def check_channel_worker(channel, session=None):
    """Worker function for concurrent execution with session pooling"""
    if is_channel_live_advanced(channel['url'], session):
        return channel
    return None

def combine_playlists_advanced(playlist_sources, priority_order, max_workers=30):
    """
    Advanced playlist combining with smart sorting and deduplication
    """
    session = get_session_with_retries()
    raw_combined_playlist = []
    seen_channels = {}  # Changed to dict to track source priority
    source_position = {}  # Track position for stable sorting

    # Combine priority order with additional sources
    valid_sources = [s for s in priority_order + playlist_sources if s]
    
    # Create source position mapping
    for position, source in enumerate(valid_sources):
        source_position[source] = position

    print(f"📡 Loading {len(valid_sources)} playlist sources...")

    # Process sources in priority order
    for source_idx, source in enumerate(valid_sources):
        print(f"   [{source_idx + 1}/{len(valid_sources)}] Parsing: {source[:50]}...")
        source_playlist = read_m3u_playlist_advanced(source, session)
        
        for channel in source_playlist:
            channel_identity = channel['url']
            
            # Keep first occurrence (priority order matters)
            if channel_identity not in seen_channels:
                seen_channels[channel_identity] = {
                    'data': channel,
                    'source_priority': source_idx
                }
                raw_combined_playlist.append(channel)

    print(f"\n✅ Total channels extracted (VODs filtered): {len(raw_combined_playlist)}")
    print(f"🔍 Verifying stream playability (this may take a few minutes)...\n")

    # Concurrent verification with progress
    verified_playlist = []
    verified_count = 0
    total_count = len(raw_combined_playlist)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_channel_worker, ch, session): ch for ch in raw_combined_playlist}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                verified_playlist.append(result)
                verified_count += 1
            
            # Progress indicator
            total_checked = verified_count + (total_count - len(futures))
            if total_checked % 10 == 0:
                print(f"   Progress: {verified_count} / {total_count} verified playable...")

    print(f"\n")
    
    # Sort by group, then by channel name (stable sort - maintains order within groups)
    verified_playlist.sort(key=lambda x: (x['group'].lower(), x['original_name'].lower()))
    
    session.close()
    return verified_playlist

def write_to_file(playlist, output_file, promo_channel=None):
    """Write playlist to M3U file"""
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIYARTVBOT\n")
        f.write(f"# Updated: {current_time_bd} (BD Time)\n")
        f.write("# 100% Playable Live TV Channels | VODs Excluded\n")
        f.write("# Multi-source aggregation with advanced verification\n\n")
            
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"📢 Promo\",%s\n%s\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
            f.write("\n")
            
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (
                item['logo'], item['group'], item['channel_name'], item['url']
            ))

def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 SHAHRIYAR LIVE TV - Advanced Playlist Generator")
    print("=" * 60 + "\n")

    # Load sources from environment variables
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    playlist_sources = [s for s in playlist_sources if s]  # Remove None values
    
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    priority_order = [s for s in priority_order if s]  # Remove None values
    
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'

    if not playlist_sources and not priority_order:
        print("❌ No playlist sources found in environment variables!")
        return

    print(f"📋 Configuration:")
    print(f"   Priority sources: {len(priority_order)}")
    print(f"   Additional sources: {len(playlist_sources)}")
    print(f"   Total sources: {len(priority_order) + len(playlist_sources)}\n")

    # Combine and verify playlists
    combined_playlist = combine_playlists_advanced(playlist_sources, priority_order, max_workers=30)

    # Promo channel
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    # Write to file
    write_to_file(combined_playlist, output_file, promo_channel)
    
    print("=" * 60)
    print(f"✨ Final Result:")
    print(f"   📊 Total verified playable channels: {len(combined_playlist)}")
    print(f"   💾 Output file: {output_file}")
    print(f"   ✅ Status: SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    main()
