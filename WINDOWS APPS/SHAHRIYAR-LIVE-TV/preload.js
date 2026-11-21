const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    setHeaders: (data) => ipcRenderer.send('set-stream-headers', data)
});