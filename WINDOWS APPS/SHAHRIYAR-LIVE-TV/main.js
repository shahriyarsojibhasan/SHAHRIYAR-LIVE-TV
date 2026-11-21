const { app, BrowserWindow, ipcMain, session } = require('electron');
const path = require('path');

// 🚀 FIX: SSL Handshake Error (-101) & Hardware Acceleration
app.commandLine.appendSwitch('ignore-certificate-errors');
app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors');
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');

let activeHeaders = {};
let targetDomain = '';

function createWindow() {
    const win = new BrowserWindow({
        width: 1280,
        height: 720,
        autoHideMenuBar: true,
        icon: path.join(__dirname, 'icon.ico'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: false // CORS Bypass
        }
    });

    // 🚀 Advanced Network Request Interceptor for Dynamic Pipe Headers
    session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
        const requestHeaders = { ...details.requestHeaders };

        if (targetDomain && details.url.includes(targetDomain)) {
            for (const [key, value] of Object.entries(activeHeaders)) {
                requestHeaders[key] = value;
            }
        }

        callback({ requestHeaders: requestHeaders });
    });

    win.loadFile('index.html');
}

app.whenReady().then(() => {
    ipcMain.on('set-stream-headers', (event, data) => {
        if (data.url) {
            try {
                targetDomain = new URL(data.url).hostname; 
            } catch (e) {
                targetDomain = '';
            }
        }
        activeHeaders = data.headers || {};
    });

    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});