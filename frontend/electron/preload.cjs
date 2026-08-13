const { contextBridge, ipcRenderer } = require('electron');

// Expose safe desktop capabilities to the React renderer
contextBridge.exposeInMainWorld('syraDesktop', {
	isDesktop: true,
	platform: process.platform,
	minimize: () => ipcRenderer.send('window-minimize'),
	maximize: () => ipcRenderer.send('window-maximize'),
	close: () => ipcRenderer.send('window-close'),
	sendNotification: (title, body) => ipcRenderer.send('desktop-notification', { title, body }),
});
