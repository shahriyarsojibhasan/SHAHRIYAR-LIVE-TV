const express = require('express');
const fetch = require('node-fetch');
const path = require('path');
const app = express();

// ✅ CORS Middleware - সব request এ
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS, POST');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range');
    res.header('Access-Control-Expose-Headers', 'Content-Length, Content-Range');
    
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// ✅ Static files serve
app.use(express.static(path.join(__dirname)));

// ✅ Home route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// ✅ TS to M3U8 Master Playlist Converter - প্লেলিস্ট generate করে
app.get('/master.m3u8', async (req, res) => {
    const tsUrl = req.query.url;
    
    console.log('✅ M3U8 Request:', tsUrl);
    
    if (!tsUrl) {
        return res.status(400).send('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST');
    }
    
    try {
        // M3U8 playlist তে নিজের stream proxy endpoint দাও
        const streamProxyUrl = `${req.protocol}://${req.get('host')}/stream?url=${encodeURIComponent(tsUrl)}`;
        
        const m3u8Content = `#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:EVENT
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
${streamProxyUrl}
#EXT-X-ENDLIST`;

        res.set({
            'Content-Type': 'application/vnd.apple.mpegurl; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        });
        
        console.log('📡 Sending M3U8 Playlist');
        res.send(m3u8Content);
        
    } catch (error) {
        console.error('❌ M3U8 Error:', error.message);
        res.status(500).send('#EXTM3U\n#EXT-X-ENDLIST');
    }
});

// ✅ Stream Proxy - সরাসরি TS stream serve করে CORS headers সহ
app.get('/stream', async (req, res) => {
    const tsUrl = req.query.url;
    
    console.log('🎬 Stream Request:', tsUrl);
    
    if (!tsUrl) {
        return res.status(400).send('Missing URL');
    }
    
    try {
        console.log('🔄 Fetching stream from:', tsUrl);
        
        const requestOptions = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            },
            timeout: 300000 // 5 minutes
        };
        
        const response = await fetch(tsUrl, requestOptions);
        
        if (!response.ok) {
            console.error('❌ Stream Error:', response.status);
            return res.status(response.status).send('Stream unavailable');
        }
        
        // Headers set করো
        res.set({
            'Content-Type': response.headers.get('content-type') || 'video/mp2t',
            'Content-Length': response.headers.get('content-length') || '',
            'Cache-Control': 'public, max-age=3600',
            'Accept-Ranges': 'bytes'
        });
        
        console.log('✅ Streaming started');
        
        // Stream করো
        response.body.pipe(res);
        
        response.body.on('error', (error) => {
            console.error('❌ Stream Error:', error.message);
            res.end();
        });
        
        res.on('error', (error) => {
            console.error('❌ Response Error:', error.message);
            response.body.destroy();
        });
        
    } catch (error) {
        console.error('❌ Proxy Error:', error.message);
        res.status(500).send('Proxy Error: ' + error.message);
    }
});

// ✅ Direct Proxy (পুরানো method)
app.get('/proxy', async (req, res) => {
    const url = req.query.url;
    
    console.log('🔗 Proxy Request:', url);
    
    if (!url) {
        return res.status(400).send('Missing URL');
    }
    
    try {
        const requestOptions = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            },
            timeout: 300000
        };
        
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
            console.error('❌ Proxy Error:', response.status);
            return res.status(response.status).send('Stream unavailable');
        }
        
        res.set({
            'Content-Type': response.headers.get('content-type') || 'video/mp2t',
            'Content-Length': response.headers.get('content-length') || ''
        });
        
        response.body.pipe(res);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        res.status(500).send('Error: ' + error.message);
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

// ✅ Error Handler
app.use((err, req, res, next) => {
    console.error('❌ Error:', err);
    res.status(500).send('Internal Server Error');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 Server Running on Port ${PORT}`);
    console.log(`📺 Open: http://localhost:${PORT}`);
    console.log(`🎬 M3U8: http://localhost:${PORT}/master.m3u8?url=TS_URL`);
    console.log(`📡 Stream: http://localhost:${PORT}/stream?url=TS_URL`);
    console.log(`💚 Health: http://localhost:${PORT}/health\n`);
});
