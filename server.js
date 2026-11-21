// ========================================================
// 📺 SHAHRIYAR LIVE TV - Local / Node.js Streaming Server
// 🚀 High-Performance HLS Segment Rewriting Proxy
// ========================================================

const express = require('express');
const fetch = require('node-fetch');
const path = require('path');
const app = express();

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS, POST',
    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range',
    'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Content-Type'
};

// CORS Middleware
app.use((req, res, next) => {
    Object.entries(corsHeaders).forEach(([k, v]) => res.header(k, v));
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
});

// Serve Static Frontend
app.use(express.static(path.join(__dirname)));

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'online ✅',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
    });
});

// Universal Proxy endpoint (/proxy or /stream)
const handleProxy = async (req, res) => {
    const targetUrl = req.query.url;
    if (!targetUrl) return res.status(400).send('Error: Missing "url" parameter');

    let parsedTarget;
    try {
        parsedTarget = new URL(targetUrl);
    } catch (e) {
        return res.status(400).send('Error: Invalid URL');
    }

    req.socket.setTimeout(0);
    res.setTimeout(0);

    const controller = new AbortController();
    req.on('close', () => controller.abort());

    try {
        const fetchHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 VLC/3.0.20',
            'Accept': '*/*',
            'Referer': parsedTarget.origin + '/',
            'Origin': parsedTarget.origin
        };

        if (req.headers.range) {
            fetchHeaders['Range'] = req.headers.range;
        }

        const response = await fetch(targetUrl, {
            headers: fetchHeaders,
            signal: controller.signal
        });

        if (!response.ok && response.status !== 206) {
            return res.status(response.status).send(`Stream error: Upstream status ${response.status}`);
        }

        const contentType = (response.headers.get('content-type') || '').toLowerCase();
        const isM3U8 = targetUrl.toLowerCase().includes('.m3u8') || targetUrl.toLowerCase().includes('.m3u') || contentType.includes('mpegurl');

        // M3U8 Segment rewriting
        if (isM3U8) {
            const rawText = await response.text();
            const serverOrigin = `${req.protocol}://${req.get('host')}`;
            const baseUrl = targetUrl;

            const rewritten = rawText.split('\n').map(line => {
                const trimmed = line.trim();
                if (!trimmed) return line;

                if (trimmed.startsWith('#')) {
                    return line.replace(/URI=["']([^"']+)["']/gi, (m, keyUri) => {
                        try {
                            const absKey = new URL(keyUri, baseUrl).href;
                            return `URI="${serverOrigin}/proxy?url=${encodeURIComponent(absKey)}"`;
                        } catch {
                            return m;
                        }
                    });
                }

                try {
                    const abs = new URL(trimmed, baseUrl).href;
                    return `${serverOrigin}/proxy?url=${encodeURIComponent(abs)}`;
                } catch {
                    return line;
                }
            }).join('\n');

            res.set({
                'Content-Type': 'application/vnd.apple.mpegurl; charset=utf-8',
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0'
            });
            return res.send(rewritten);
        }

        // Binary streaming (.ts / .mp4 / audio)
        res.status(response.status);
        res.setHeader('Content-Type', contentType || 'video/mp2t');
        res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
        
        const cl = response.headers.get('content-length');
        if (cl) res.setHeader('Content-Length', cl);

        const cr = response.headers.get('content-range');
        if (cr) res.setHeader('Content-Range', cr);

        response.body.pipe(res);
        response.body.on('error', (err) => {
            if (err.name !== 'AbortError') console.error('Stream pipe error:', err.message);
            res.end();
        });

    } catch (err) {
        if (err.name !== 'AbortError') {
            console.error('Proxy Error:', err.message);
            if (!res.headersSent) res.status(500).send('Proxy Error: ' + err.message);
        }
    }
};

app.get('/proxy', handleProxy);
app.get('/stream', handleProxy);

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 SHAHRIYAR LIVE TV Server running on port ${PORT}`);
    console.log(`📺 Frontend: http://localhost:${PORT}`);
    console.log(`📡 Stream Proxy: http://localhost:${PORT}/proxy?url=YOUR_STREAM_URL\n`);
});
