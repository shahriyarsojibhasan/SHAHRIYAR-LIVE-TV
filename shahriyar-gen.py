import os
import requests
import concurrent.futures
from datetime import datetime, timezone, timedelta
import random

# ==================== MULTIPLE USER-AGENTS FOR BETTER COMPATIBILITY ====================
# This list helps bypass stricter servers that check User-Agent headers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
]

# ==================== COMPREHENSIVE HEADERS WITH CORS SUPPORT ====================
# These headers help with CORS issues and make requests more authentic
def get_headers():
    """
    Generate random headers for each request to avoid detection and bypass rate limiting.
    Includes CORS headers and comprehensive Accept headers.
    """
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        # CORS Headers
        'Origin': 'https://github.com',
        'Referer': 'https://github.com/',
    }


def is_vod(url):
    """
    Checks if a URL is a VOD (Movie/Series) instead of a Live TV channel.
    
    Logic:
    - VODs typically use specific file extensions (.mp4, .mkv, .avi, .m4v, .mov)
    - Xtream Codes API usually contains '/movie/' or '/series/' paths for VODs
    
    Args:
        url (str): The streaming URL to check
        
    Returns:
        bool: True if URL is a VOD, False if it's Live TV
    """
    url_lower = url.lower()
    
    # Common VOD file extensions - Check if URL ends with media file extension
    vod_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv']
    if any(url_lower.endswith(ext) for ext in vod_extensions):
        return True
        
    # Common VOD paths in Xtream Codes API format
    # If URL contains /movie/ or /series/, it's typically VOD content
    if '/movie/' in url_lower or '/series/' in url_lower:
        return True
        
    return False


def is_channel_live(url):
    """
    Enhanced stream verification with multiple checks and robust error handling.
    
    Verification Process:
    1. Send HEAD/GET request to check if server responds
    2. Verify Content-Type header contains valid media type
    3. Attempt to read initial stream data (chunk verification)
    4. Validate HTTP status codes
    5. Handle CORS and redirect responses
    
    Args:
        url (str): The streaming URL to verify
        
    Returns:
        bool: True if stream is playable, False otherwise
    """
    if not url or not url.startswith('http'):
        return False
    
    try:
        # Try different request methods and timeouts for robustness
        for attempt in range(2):
            try:
                # First attempt: GET request with stream=True
                if attempt == 0:
                    response = requests.get(
                        url,
                        headers=get_headers(),
                        stream=True,
                        timeout=10,
                        allow_redirects=True,
                        verify=False  # Disable SSL verification for HTTPS issues
                    )
                # Second attempt: HEAD request if GET fails (faster, less bandwidth)
                else:
                    response = requests.head(
                        url,
                        headers=get_headers(),
                        timeout=8,
                        allow_redirects=True,
                        verify=False
                    )
                
                # Check if response status indicates success
                if response.status_code in [200, 206, 301, 302, 307, 308]:
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # Valid media content types for streaming
                    valid_media_types = [
                        'video',           # video/mp4, video/x-msvideo, etc.
                        'audio',           # audio/mpeg, audio/aac, etc.
                        'application/x-mpegURL',  # HLS playlists
                        'application/vnd.apple.mpegurl',  # HLS variant
                        'application/dash+xml',   # DASH manifests
                        'application/octet-stream',  # Generic binary streams
                        'text/plain',      # Some streams serve as plain text
                        'text/html',       # Some streaming sites use HTML
                    ]
                    
                    # If Content-Type matches valid types or is empty (some streams don't send it)
                    if any(media_type in content_type for media_type in valid_media_types) or not content_type:
                        # Try to read initial chunk to verify actual stream data exists
                        try:
                            for chunk in response.iter_content(chunk_size=1024):
                                if chunk:  # If we got data, stream is valid
                                    return True
                        except Exception:
                            # If chunk reading fails on first attempt, try HEAD request
                            if attempt == 0:
                                continue
                            return False
                        
                        # If no chunks but status was good and content-type valid, consider it valid
                        return True
                
                # Handle redirect responses (follow chain)
                elif response.status_code in [301, 302, 307, 308]:
                    return is_channel_live(response.headers.get('location', ''))
                
            except requests.Timeout:
                # Timeout on this attempt, try next method
                if attempt == 0:
                    continue
                return False
            except requests.ConnectionError:
                if attempt == 0:
                    continue
                return False
        
        return False
        
    except Exception as e:
        # Generic error handling - log and return False
        print(f"Stream verification error for {url}: {str(e)[:50]}")
        return False
    finally:
        # Ensure connection is properly closed
        try:
            if 'response' in locals():
                response.close()
        except Exception:
            pass


def read_m3u_playlist(source):
    """
    Bulletproof Line-by-Line M3U parser with comprehensive channel extraction.
    
    Features:
    - Handles both URL and local file sources
    - Robust line-by-line parsing
    - Extracts logos, group titles, and channel names
    - Filters out unwanted content (VODs, movies, blocked keywords)
    - Applies custom branding to channels
    
    Args:
        source (str): URL or file path to M3U playlist
        
    Returns:
        list: List of channel dictionaries with 'logo', 'group', 'channel_name', 'url'
    """
    playlist = []
    if not source:
        return []

    content = ""
    
    # ==================== FETCH CONTENT FROM SOURCE ====================
    if source.startswith("http"):
        # Source is a URL - fetch with enhanced headers and error handling
        try:
            response = requests.get(
                source,
                headers=get_headers(),
                timeout=15,
                verify=False,  # Handle SSL issues
                allow_redirects=True
            )
            response.encoding = 'utf-8'  # Ensure UTF-8 decoding
            content = response.text
        except requests.RequestException as e:
            print(f"Error fetching playlist from {source}: {e}")
            return []
    else:
        # Source is a local file - read with UTF-8 encoding
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading file {source}: {e}")
            return []

    # ==================== NORMALIZE AND PARSE LINES ====================
    # Convert all line endings to \n for consistent parsing
    lines = content.replace('\r\n', '\n').split('\n')
    
    # Keywords to block (unwanted channels/groups)
    blocked_keywords = ['himel op', 'promo', 'playz tv', 'test', 'dummy']
    current_channel = {}

    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # ==================== PARSE #EXTINF HEADER ====================
        if line.startswith('#EXTINF:'):
            # Extract Logo URL from tvg-logo attribute
            logo_start = line.find('tvg-logo="')
            if logo_start != -1:
                logo_end = line.find('"', logo_start + 10)
                current_channel['logo'] = line[logo_start + 10:logo_end]
            else:
                current_channel['logo'] = ""

            # Extract Group Title from group-title attribute
            # This categorizes channels (Sports, News, Entertainment, etc.)
            group_start = line.find('group-title="')
            if group_start != -1:
                group_end = line.find('"', group_start + 13)
                current_channel['group'] = line[group_start + 13:group_end]
            else:
                current_channel['group'] = "Uncategorized"

            # Extract Channel Name - usually after the last comma
            name_split = line.split(',')
            current_channel['name'] = name_split[-1].strip() if len(name_split) > 1 else "Unknown Channel"

        # ==================== PARSE STREAMING URL ====================
        elif line.startswith('http'):
            if current_channel:
                url = line
                name_lower = current_channel['name'].lower()
                group_lower = current_channel['group'].lower()
                url_lower = url.lower()

                # ========== FILTER 1: BLOCK UNWANTED KEYWORDS ==========
                # Skip channels with blocked keywords in name, group, or URL
                if any(kw in name_lower or kw in group_lower or kw in url_lower for kw in blocked_keywords):
                    current_channel = {}
                    continue
                
                # ========== FILTER 2: BLOCK MOVIES & SERIES (VODs) ==========
                # Skip VOD content - keep only Live TV channels
                if is_vod(url):
                    current_channel = {}
                    continue

                # ========== APPLY BRANDING & ADD TO PLAYLIST ==========
                # Add custom branding to channel name for identification
                branded_name = f"{current_channel['name']} | SHAHRIYAR LIVE TV"
                
                playlist.append({
                    'logo': current_channel['logo'],
                    'group': current_channel['group'],
                    'channel_name': branded_name,
                    'url': url
                })
                
                # Reset for next channel
                current_channel = {}

    return playlist


def check_channel_worker(channel):
    """
    Worker function for concurrent stream verification.
    Used by ThreadPoolExecutor to verify multiple channels in parallel.
    
    Args:
        channel (dict): Channel dictionary with 'url' key
        
    Returns:
        dict: Channel dictionary if stream is valid, None if invalid
    """
    if is_channel_live(channel['url']):
        return channel
    return None


def combine_playlists(playlist_sources, priority_order):
    """
    Combines multiple M3U playlists with priority ordering and deduplication.
    
    Features:
    - Reads multiple playlist sources (URLs and files)
    - Maintains priority order - sources listed first take precedence
    - Deduplicates channels by URL (prevents duplicates)
    - Verifies each stream is live and accessible
    - Uses concurrent verification for speed (20 parallel threads)
    
    Args:
        playlist_sources (list): List of playlist URLs/files to combine
        priority_order (list): List of priority sources (checked first)
        
    Returns:
        list: Combined and verified playlist of live channels
    """
    raw_combined_playlist = []
    seen_channels = set()

    # Combine priority and regular sources, filter out None values
    valid_sources = [s for s in priority_order + playlist_sources if s]

    # ==================== READ ALL PLAYLISTS ====================
    # Iterate through sources in priority order
    for source in valid_sources:
        source_playlist = read_m3u_playlist(source)
        
        # Add channels from this source, skipping duplicates
        for channel in source_playlist:
            channel_identity = channel['url']  # Use URL as unique identifier
            
            # Only add if we haven't seen this URL before (deduplication)
            if channel_identity not in seen_channels:
                seen_channels.add(channel_identity)
                raw_combined_playlist.append(channel)

    # ==================== VERIFY STREAMS CONCURRENTLY ====================
    combined_playlist = []
    print(f"Total Live TV channels extracted (Movies skipped): {len(raw_combined_playlist)}. Verifying stream status... 🚀")

    # Use ThreadPoolExecutor for concurrent stream verification (20 parallel threads)
    # This significantly speeds up the verification process
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check_channel_worker, raw_combined_playlist)
        
        # Collect results - only add channels that verified successfully
        for channel in results:
            if channel is not None:
                combined_playlist.append(channel)

    return combined_playlist


def write_to_file(playlist, output_file, promo_channel=None):
    """
    Writes the final playlist to M3U file with headers and metadata.
    
    M3U Format:
    - #EXTM3U header
    - #EXTINF metadata (logo, group, name)
    - Stream URL
    
    Features:
    - Includes creation timestamp (BD timezone)
    - Adds promo channel at top
    - Includes author credits and update info
    - Properly formatted for media players (VLC, Kodi, etc.)
    
    Args:
        playlist (list): List of verified channel dictionaries
        output_file (str): Output M3U file path
        promo_channel (dict): Optional promo channel to add at top
    """
    # Get current time in Bangladesh timezone (UTC+6)
    bd_timezone = timezone(timedelta(hours=6))
    current_time_bd = datetime.now(bd_timezone).strftime('%Y-%m-%d %H:%M:%S')

    with open(output_file, 'w', encoding='utf-8') as f:
        # ==================== WRITE M3U HEADER ====================
        f.write("#EXTM3U\n")
        f.write("# By SHAHRIYAR SOJIB HASAN\n")
        f.write("# TELEGRAM @SHAHRIAYRTVBOT\n")
        f.write(f"# Update on {current_time_bd} (BD Time)\n")
        f.write("# Note: Please Don't Use Without Credits\n")
        f.write("# Note: I do not host any content, everything is publicly available. And any issues, please contact me.\n\n")
        
        # ==================== WRITE PROMO CHANNEL ====================
        if promo_channel:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"Promo\",%s\n%s\n" % (
                promo_channel['logo'], promo_channel['channel_name'], promo_channel['url']
            ))
        
        # ==================== WRITE ALL CHANNELS ====================
        # Each channel has metadata (EXTINF) followed by URL
        for item in playlist:
            f.write("#EXTINF:-1 tvg-logo=\"%s\" group-title=\"%s\",%s\n%s\n" % (
                item['logo'], item['group'], item['channel_name'], item['url']
            ))


if __name__ == "__main__":
    # ==================== LOAD CONFIGURATION FROM ENVIRONMENT ====================
    # Playlist sources from environment variables (PLAYLIST_SOURCE_URL_1 to _20)
    playlist_sources = [os.getenv(f'PLAYLIST_SOURCE_URL_{i}') for i in range(1, 21)]
    
    # Priority sources that are checked first (PRIORITY_PLAYLIST_URL_1 to _10)
    priority_order = [os.getenv(f'PRIORITY_PLAYLIST_URL_{i}') for i in range(1, 11)]
    
    # Output file name
    output_file = 'SHAHRIYAR-LIVE-TV.m3u'

    # ==================== COMBINE AND VERIFY PLAYLISTS ====================
    combined_playlist = combine_playlists(playlist_sources, priority_order)

    # ==================== PROMO CHANNEL CONFIGURATION ====================
    promo_channel = {
        'logo': 'https://camo.githubusercontent.com/80ae2e5389a61f88a909165f57b1d44d66ffa1337d25accd421e839e26c02472/68747470733a2f2f692e6962622e636f2e636f6d2f54465373736d572f696d6167652e706e67',
        'channel_name': 'SHAHRIYAR LIVE TV',
        'url': 'https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/raw/refs/heads/main/assest/shahriyarlivetv.m3u8'
    }

    # ==================== WRITE FINAL PLAYLIST ====================
    write_to_file(combined_playlist, output_file, promo_channel)
    
    # ==================== FINAL REPORT ====================
    print(f"Final valid Live TV channels: {len(combined_playlist)}")
    print(f"Playlist saved to: {output_file}")
