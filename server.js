const express = require('express');
const fetch = require('node-fetch');
const path = require('path');
const app = express();

// ✅ CORS Middleware
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS, POST');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range');
    
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

app.use(express.static(path.join(__dirname)));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'home.html'));
});

// ✅ M3U8 Master Playlist Proxy (Unplayable লিংকের জন্য)
app.get('/master.m3u8', async (req, res) => {
    const tsUrl = req.query.url;
    console.log('✅ M3U8 Request:', tsUrl);
    
    if (!tsUrl) {
        return res.status(400).send('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST');
    }
    
    try {
        const streamProxyUrl = `${req.protocol}://${req.get('host')}/stream?url=${encodeURIComponent(tsUrl)}`;
        
        const m3u8Content = `#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:999999
#EXT-X-MEDIA-SEQUENCE:1
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:999999.000,
${streamProxyUrl}
#EXT-X-ENDLIST`;

        res.set({
            'Content-Type': 'application/vnd.apple.mpegurl; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Access-Control-Allow-Origin': '*'
        });
        
        res.send(m3u8Content);
    } catch (error) {
        console.error('❌ M3U8 Error:', error.message);
        res.status(500).send('#EXTM3U\n#EXT-X-ENDLIST');
    }
});

// ✅ Stream Proxy - 15s Stop Fix
app.get('/stream', async (req, res) => {
    const tsUrl = req.query.url;
    console.log('🎬 Stream Request:', tsUrl);
    
    if (!tsUrl) {
        return res.status(400).send('Missing URL');
    }

    // 🚀 FIX 1: Disable Node.js Server Timeouts for Endless Live Stream
    req.socket.setTimeout(0);
    res.setTimeout(0);

    const controller = new AbortController();
    const signal = controller.signal;

    req.on('close', () => {
        console.log('🛑 Client disconnected, aborting stream...');
        controller.abort();
    });
    
    try {
        const requestOptions = {
            headers: {
                'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            },
            signal
        };
        
        const response = await fetch(tsUrl, requestOptions);
        
        if (!response.ok) {
            console.error('❌ Stream Error:', response.status);
            return res.status(response.status).send('Stream unavailable');
        }
        
        // 🚀 FIX 2: Live Stream Headers Customization
        // Content-Length পাঠানো যাবে না, তাহলে ব্রাউজার ১৫ সেকেন্ড পর থেমে যাবে!
        res.setHeader('Content-Type', 'video/mp2t');
        res.setHeader('Transfer-Encoding', 'chunked'); // Force endless chunks
        res.setHeader('Connection', 'keep-alive');
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0');
        
        console.log('✅ Streaming started without timeout restrictions');
        
        // Stream data to client
        response.body.pipe(res);
        
        response.body.on('error', (error) => {
            if (error.name !== 'AbortError') {
                console.error('❌ Upstream Error:', error.message);
            }
            res.end();
        });
        
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('🛑 Fetch aborted successfully.');
        } else {
            console.error('❌ Proxy Error:', error.message);
            if (!res.headersSent) {
                res.status(500).send('Proxy Error: ' + error.message);
            }
        }
    }
});

// ✅ Health Check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'running ✅',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// ✅ Global Error Handler
app.use((err, req, res, next) => {
    console.error('❌ Global Error:', err);
    if (!res.headersSent) {
        res.status(500).send('Internal Server Error');
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 Server Running on Port ${PORT}`);
    console.log(`📺 Open: http://localhost:${PORT}`);
    console.log(`📡 TS Proxy: http://localhost:${PORT}/stream?url=YOUR_TS_URL`);
    console.log(`💚 Health: http://localhost:${PORT}/health\n`);
});