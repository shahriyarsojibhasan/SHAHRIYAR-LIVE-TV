import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import time
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced User-Agent rotation to prevent blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

def get_headers(index=0):
    """Rotate User-Agent headers"""
    return {
        'User-Agent': USER_AGENTS[index % len(USER_AGENTS)],
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
    }

def is_vod(url):
    """
    Enhanced VOD detection with more patterns
    """
    url_lower = url.lower()
    
    # Common VOD file extensions
    vod_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm']
    if any(url_lower.endswith(ext) for ext in vod_extensions):
        return True
    
    # Common VOD paths in Xtream Codes API & others
    vod_patterns = ['/movie/', '/series/', '/vod/', '/films/', '/tvshows/', '/episodes/', 
                    '/content/movie', '/content/series', '/get/movie', '/get/series',
                    '/live/movie', '/live/series', 'movie=', 'series=', 'vod=']
    if any(pattern in url_lower for pattern in vod_patterns):
        return True
    
    return False

def is_channel_live(url, index=0):
    """
    Enhanced stream verification with better timeout handling
    """
    try:
        response = requests.get(
            url, 
            headers=get_headers(index), 
            stream=True, 
            timeout=8,
            allow_redirects=True,
            verify=False
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            content_length = response.headers.get('Content-Length', '')
            
            # Accept wider range of media types
            valid_media_types = [
                'video', 'audio', 'mpegurl', 'dash+xml', 'octet-stream',
                'application/x-mpegURL', 'application/vnd.apple.mpegurl',
                'text/plain', 'application/json', 'binary'
            ]
            
            # Check if content_type matches or is empty (many streams return empty)
            is_valid_type = not content_type or any(
                media_type in content_type for media_type in valid_media_types
            )
            
            if is_valid_type:
                try:
                    # Try to read first chunk
                    chunk = next(response.iter_content(chunk_size=1024), None)
                    if chunk and len(chunk) > 0:
                        return True
                except (StopIteration, Exception):
                    # Some streams might not return data immediately but still be valid
                    if content_length:  # If Content-Length header exists, consider it valid
                        return True
        
        # Additional check: Some streams return 200 but need specific handling
        if response.status_code in [200, 206]:
            return True
            
        return False
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        logger.debug(f"Error checking {url}: {str(e)}")
        return False
    finally:
        try:
            if 'response' in locals():
                response.close()
        except:
            pass

def extract_m3u_data(content):
    """
    Enhanced M3U parser with better line-by-line extraction
    """
    channels = []
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    current_channel = {}
    blocked_keywords = ['himel op', 'promo', 'playz tv', 'advertisement', 'ads']
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        if line.startswith('#EXTINF:'):
            # Extract Logo
            logo = ""
            logo_start = line.find('tvg-logo="')
            if logo_start != -1:
                logo_end = line.find('"', logo_start + 10)
                if logo_end != -1:
                    logo = line[logo_start + 10:logo_end]
            
            # Extract Group Title
            group = "Uncategorized"
            group_start = line.find('group-title="')
            if group_start != -1:
                group_end = line.find('"', group_start + 13)
                if group_end != -1:
                    group = line[group_start + 13:group_end]
            
            # Extract Channel Name
            name = "Unknown Channel"
            comma_index = line.rfind(',')
            if comma_index != -1:
                name = line[comma_index + 1:].strip()
            
            current_channel = {
                'logo': logo,
                'group': group,
                'name': name
            }
        
        elif line.startswith('http://') or line.startswith('https://'):
            if current_channel and 'name' in current_channel:
                url = line
                
                # Filter checks
                name_lower = current_channel['name'].lower()
                group_lower = current_channel['group'].lower()
                url_lower = url.lower()
                
                # Skip blocked keywords
                if any(kw in name_lower or kw in group_lower or kw in url_lower for kw in blocked_keywords):
                    current_channel = {}
                    i += 1
                    continue
                
                # Skip VODs
                if is_vod(url):
                    current_channel = {}
                    i += 1
                    continue
                
                # Valid channel
                channels.append({
                    'logo': current_channel['logo'],
                    'group': current_channel['group'],
                    'name': current_channel['name'],
                    'url': url
                })
            
            current_channel = {}
        
        i += 1
    
    return channels

def read_m3u_playlist(source, index=0):
    """
    Read M3U playlist from URL or file with enhanced error handling
    """
    if not source:
        return []
    
    try:
        content = ""
        if source.startswith("http"):
            try:
                response = requests.get(
                    source, 
                    headers=get_headers(index), 
                    timeout=20,
                    verify=False
                )
                response.encoding = 'utf-8'
                content = response.text
            except requests.RequestException as e:
                logger.warning(f"Error fetching {source}: {e}")
                return []
        else:
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()
            except IOError as e:
                logger.warning(f"Error reading {source}: {e}")
                return []
        
        if not content:
            return []
        
        return extract_m3u_data(content)
    
    except Exception as e:
        logger.error(f"Error processing {source}: {e}")
        return []

def check_channel_worker(args):
    """Worker function for concurrent stream verification"""
    channel, index = args
    if is_channel_live(channel['url'], index):
        return channel
    return None

def combine_playlists(playlist_sources, priority_order):
    """
    Combine playlists with priority handling and deduplication
    """
    raw_combined_playlist = []
    seen_urls = set()
    channel_count = {}

    # Process priority sources first (they get more weight)
    valid_priority = [s for s in priority_order if s]
    valid_regular = [s for s in playlist_sources if s]
    
    print(f"\n📊 Processing {len(valid_priority)} priority sources...")
    for idx, source in enumerate(valid_priority):
        playlist = read_m3u_playlist(source, idx)
        print(f"   Priority Source {idx + 1}: {len(playlist)} channels extracted")
        for channel in playlist:
            if channel['url'] not in seen_urls:
                seen_urls.add(channel['url'])
                channel['priority'] = 1  # Mark as priority
                raw_combined_playlist.append(channel)
                channel_count[source] = channel_count.get(source, 0) + 1
    
    print(f"\n📊 Processing {len(valid_regular)} regular sources...")
    for idx, source in enumerate(valid_regular):
        playlist = read_m3u_playlist(source, idx + len(valid_priority))
        print(f"   Regular Source {idx + 1}: {len(playlist)} channels extracted")
        for channel in playlist:
            if channel['url'] not in seen_urls:
                seen_urls.add(channel['url'])
                channel['priority'] = 0
                raw_combined_playlist.append(channel)
                channel_count[source] = channel_count.get(source, 0) + 1
    
    print(f"\n✅ Total unique channels before verification: {len(raw_combined_playlist)}")
    print(f"🚀 Verifying stream status (this may take a few minutes)...")
    
    combined_playlist = []
    processed = 0
    
    # Verify streams concurrently with better worker distribution
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        # Create indexed arguments for workers
        worker_args = [(channel, idx % 30) for idx, channel in enumerate(raw_combined_playlist)]
        
        futures = {executor.submit(check_channel_worker, args): args for args in worker_args}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                channel = future.result()
                if channel is not None:
                    combined_playlist.append(channel)
                    processed += 1
                    
                    if processed % 20 == 0:
                        print(f"   ✓ Verified {processed} live channels so far...")
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    print(f"✅ Total verified live channels: {len(combined_playlist)}")
    return combined_playlist

def write_to_file(playlist, output_file, promo_channel=None):
    """Write verified playlist to M3U file"""
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIYARTVBOT\n")
        f.write(f"# Updated: {current_time_bd} (BD Time)\n")
        f.write("# Auto-filtered for Live TV only. No VODs/Movies.\n")
        f.write(f"# Total Channels: {len(playlist)}\n\n")
        
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"PROMO\",%s\n%s\n\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
        
        # Group channels by category
        grouped = {}
        for item in playlist:
            group = item['group']
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(item)
        
        # Write grouped channels
        for group in sorted(grouped.keys()):
            for item in grouped[group]:
                branded_name = f"{item['name']} | SHAHRIYAR LIVE TV"
                f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (
                    item['logo'], group, branded_name, item['url']
                ))

if __name__ == "__main__":
    # Load playlist sources from environment variables
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    
    # Filter None values
    playlist_sources = [s for s in playlist_sources if s]
    priority_order = [s for s in priority_order if s]
    
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'
    
    print("=" * 60)
    print("🎬 SHAHRIYAR LIVE TV - Channel Grabber")
    print("=" * 60)
    
    combined_playlist = combine_playlists(playlist_sources, priority_order)
    
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV 🎬',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }
    
    write_to_file(combined_playlist, output_file, promo_channel)
    
    print("\n" + "=" * 60)
    print(f"✅ Final Output: {len(combined_playlist)} live channels")
    print(f"📄 Saved to: {output_file}")
    print("=" * 60 + "\n")
