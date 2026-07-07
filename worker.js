// ✅ CORS Headers Helper
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS, POST',
  'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range'
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const { pathname, searchParams } = url;

    // ✅ 1. Handle CORS Preflight (OPTIONS)
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 200,
        headers: corsHeaders
      });
    }

    try {
      // ✅ 2. Health Check Endpoint
      if (pathname === '/health') {
        return new Response(JSON.stringify({
          status: 'running ✅',
          timestamp: new Date().toISOString(),
          platform: 'Cloudflare Worker'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // ✅ 3. M3U8 Master Playlist Proxy
      if (pathname === '/master.m3u8') {
        const tsUrl = searchParams.get('url');
        
        if (!tsUrl) {
          return new Response('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST', {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/vnd.apple.mpegurl' }
          });
        }

        const streamProxyUrl = `${url.origin}/stream?url=${encodeURIComponent(tsUrl)}`;
        
        const m3u8Content = `#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:999999\n#EXT-X-MEDIA-SEQUENCE:1\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXTINF:999999.000,\n${streamProxyUrl}\n#EXT-X-ENDLIST`;

        return new Response(m3u8Content, {
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/vnd.apple.mpegurl; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
          }
        });
      }

      // ✅ 4. Stream Proxy (Endless Live Stream with Bypass Headers)
      if (pathname === '/stream') {
        const tsUrl = searchParams.get('url');
        
        if (!tsUrl) {
          return new Response('Missing URL', { status: 400, headers: corsHeaders });
        }

        // Get actual user's IP to spoof the request
        const clientIP = request.headers.get('CF-Connecting-IP') || '1.1.1.1';
        
        // Prepare strict bypass headers
        const fetchHeaders = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) VLC/3.0.18',
          'Accept': '*/*',
          'Connection': 'keep-alive',
          'X-Forwarded-For': clientIP, // Tries to bypass Cloudflare IP blocks
          'Referer': new URL(tsUrl).origin + '/' // Some panels require exact referer
        };

        // Fetch stream from upstream server
        const upstreamResponse = await fetch(tsUrl, {
          method: request.method,
          headers: fetchHeaders,
          redirect: 'follow'
        });

        // Debugging: If stream fails, show the EXACT upstream error (e.g. 403 Forbidden)
        if (!upstreamResponse.ok) {
          return new Response(`❌ Stream blocked or unavailable.\nUpstream Server returned: ${upstreamResponse.status} ${upstreamResponse.statusText}\n\nNote: If you see 403 or 401, the IPTV provider (rgkkw.live) is actively blocking Cloudflare Worker IP addresses.`, { 
            status: upstreamResponse.status === 404 ? 404 : 502, 
            headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
          });
        }

        // Pass exact Content-Type from upstream, fallback to mp2t
        const responseHeaders = new Headers(corsHeaders);
        responseHeaders.set('Content-Type', upstreamResponse.headers.get('content-type') || 'video/mp2t');
        responseHeaders.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
        
        // Return the ReadableStream directly to the client
        return new Response(upstreamResponse.body, {
          status: upstreamResponse.status,
          headers: responseHeaders
        });
      }

      // ✅ 5. Serve Static Assets (index.html, .m3u files)
      return await env.ASSETS.fetch(request);

    } catch (error) {
      console.error('❌ Worker Error:', error.message);
      return new Response('Worker Error: ' + error.message, { 
        status: 500, 
        headers: corsHeaders 
      });
    }
  }
};