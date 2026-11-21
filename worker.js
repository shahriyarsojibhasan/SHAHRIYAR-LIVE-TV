// ========================================================
// 📺 SHAHRIYAR LIVE TV - Cloudflare Worker Edge Proxy
// 🚀 High-Performance HLS Segment Rewriter & CORS Bypass Proxy
// ========================================================

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS, POST',
  'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range',
  'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Content-Type'
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const { pathname, searchParams } = url;

    // 1. CORS Preflight (OPTIONS)
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // 2. Health Check
    if (pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'online ✅',
        service: 'SHAHRIYAR LIVE TV Edge Stream Proxy',
        timestamp: new Date().toISOString()
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 3. Universal Stream / M3U8 Proxy (/proxy or /stream)
    if (pathname === '/proxy' || pathname === '/stream') {
      const targetUrl = searchParams.get('url');
      if (!targetUrl) {
        return new Response('Error: Missing "url" parameter', {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'text/plain; charset=utf-8' }
        });
      }

      try {
        const clientIP = request.headers.get('CF-Connecting-IP') || '1.1.1.1';
        let parsedTarget;
        try {
          parsedTarget = new URL(targetUrl);
        } catch {
          return new Response('Error: Invalid URL format', { status: 400, headers: corsHeaders });
        }

        const fetchHeaders = new Headers();
        fetchHeaders.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 VLC/3.0.20');
        fetchHeaders.set('Accept', '*/*');
        fetchHeaders.set('Accept-Language', 'en-US,en;q=0.9');
        fetchHeaders.set('Referer', parsedTarget.origin + '/');
        fetchHeaders.set('Origin', parsedTarget.origin);
        fetchHeaders.set('X-Forwarded-For', clientIP);

        // Forward Range header if requested (critical for seek / video buffering)
        const rangeHeader = request.headers.get('Range');
        if (rangeHeader) {
          fetchHeaders.set('Range', rangeHeader);
        }

        const upstreamResponse = await fetch(targetUrl, {
          method: request.method === 'POST' ? 'POST' : 'GET',
          headers: fetchHeaders,
          redirect: 'follow'
        });

        if (!upstreamResponse.ok && upstreamResponse.status !== 206) {
          return new Response(`Stream error: Upstream server returned ${upstreamResponse.status} ${upstreamResponse.statusText}`, {
            status: upstreamResponse.status === 404 ? 404 : 502,
            headers: { ...corsHeaders, 'Content-Type': 'text/plain; charset=utf-8' }
          });
        }

        const contentType = (upstreamResponse.headers.get('content-type') || '').toLowerCase();
        const urlLower = targetUrl.toLowerCase();
        const isM3U8 = urlLower.includes('.m3u8') || urlLower.includes('.m3u') || contentType.includes('mpegurl');

        // 🚀 Intelligent M3U8 Parsing & Segment URL Rewriting
        if (isM3U8) {
          const rawText = await upstreamResponse.text();
          const workerOrigin = url.origin;
          const baseUrl = targetUrl;

          const rewrittenLines = rawText.split('\n').map(line => {
            const trimmed = line.trim();
            if (!trimmed) return line;

            // Handle #EXT tags with URIs (such as encryption keys)
            if (trimmed.startsWith('#')) {
              return line.replace(/URI=["']([^"']+)["']/gi, (match, keyUri) => {
                try {
                  const absoluteKeyUrl = new URL(keyUri, baseUrl).href;
                  return `URI="${workerOrigin}/proxy?url=${encodeURIComponent(absoluteKeyUrl)}"`;
                } catch {
                  return match;
                }
              });
            }

            // Normal segment or child playlist line
            try {
              const absoluteSegmentUrl = new URL(trimmed, baseUrl).href;
              return `${workerOrigin}/proxy?url=${encodeURIComponent(absoluteSegmentUrl)}`;
            } catch {
              return line;
            }
          });

          return new Response(rewrittenLines.join('\n'), {
            status: 200,
            headers: {
              ...corsHeaders,
              'Content-Type': 'application/vnd.apple.mpegurl; charset=utf-8',
              'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0'
            }
          });
        }

        // Binary streaming (.ts segments, .mp4 chunks, key files, etc.)
        const responseHeaders = new Headers(corsHeaders);
        responseHeaders.set('Content-Type', contentType || 'video/mp2t');
        responseHeaders.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
        
        const contentLength = upstreamResponse.headers.get('content-length');
        if (contentLength) responseHeaders.set('Content-Length', contentLength);

        const contentRange = upstreamResponse.headers.get('content-range');
        if (contentRange) responseHeaders.set('Content-Range', contentRange);

        return new Response(upstreamResponse.body, {
          status: upstreamResponse.status,
          headers: responseHeaders
        });

      } catch (err) {
        return new Response(`Worker Proxy Error: ${err.message}`, {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'text/plain; charset=utf-8' }
        });
      }
    }

    // 4. Serve Static Assets (index.html, .m3u files, icons)
    if (env.ASSETS) {
      return await env.ASSETS.fetch(request);
    }

    return new Response('Not Found', { status: 404, headers: corsHeaders });
  }
};
