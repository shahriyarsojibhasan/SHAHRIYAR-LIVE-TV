const express = require('express');
const fetch = require('node-fetch');
const path = require('path');
const app = express();

// ✅ Static files serve
app.use(express.static(path.join(__dirname)));

// ✅ Home route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// ✅ Proxy endpoint - with proper streaming support
app.get('/proxy', async (req, res) => {
    const url = req.query.url;
    
    console.log('Proxying URL:', url);
    
    if (!url) {
        return res.status(400).json({ error: 'URL parameter required' });
    }
    
    // Validate URL format
    try {
        new URL(url);
    } catch (e) {
        return res.status(400).json({ error: 'Invalid URL format' });
    }
    
    try {
        // Set proper headers BEFORE response starts
        res.set({
            'Content-Type': 'video/mp2t',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Transfer-Encoding': 'chunked'
        });
        
        const requestOptions = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Referer': 'https://github.com',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            },
            timeout: 60000
        };
        
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
            console.error('Stream error:', response.status, response.statusText);
            return res.status(response.status).json({ 
                error: `Stream unavailable: ${response.statusText}` 
            });
        }
        
        // Copy headers from source
        const contentType = response.headers.get('content-type');
        if (contentType) {
            res.set('Content-Type', contentType);
        }
        
        // Stream the response
        response.body.pipe(res);
        
        response.body.on('error', (error) => {
            console.error('Stream body error:', error.message);
            if (!res.headersSent) {
                res.status(500).json({ error: 'Stream read error' });
            }
        });
        
    } catch (error) {
        console.error('Proxy error:', error.message);
        
        if (!res.headersSent) {
            res.status(500).json({ 
                error: 'Proxy error: ' + error.message,
                details: process.env.NODE_ENV === 'development' ? error.stack : undefined
            });
        } else {
            res.end();
        }
    }
});

// ✅ OPTIONS endpoint for CORS
app.options('/proxy', (req, res) => {
    res.set({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.sendStatus(200);
});

// ✅ Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'running',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// ✅ Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📺 TV App: http://localhost:${PORT}`);
    console.log(`🔗 Proxy: http://localhost:${PORT}/proxy?url=STREAM_URL`);
    console.log(`💚 Health: http://localhost:${PORT}/health`);
});
