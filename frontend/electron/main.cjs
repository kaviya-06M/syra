const { app, BrowserWindow, ipcMain, Notification, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let pythonProcess = null;
const isDev = !app.isPackaged && (process.env.NODE_ENV === 'development' || !process.env.NODE_ENV);

// Check if backend is already running on port 8000
function checkBackendRunning(callback) {
	const req = http.get('http://127.0.0.1:8000/api/health', (res) => {
		callback(res.statusCode === 200);
	});
	req.on('error', () => {
		callback(false);
	});
	req.setTimeout(1000, () => {
		req.abort();
		callback(false);
	});
}

// Start Python FastAPI Backend if not already running
function startBackend() {
	checkBackendRunning((running) => {
		if (running) {
			console.log('[Electron] SYRA Backend is already running on port 8000.');
			return;
		}

		console.log('[Electron] Starting SYRA Python backend...');
		const backendPath = path.resolve(__dirname, '../backend/main.py');
		
		pythonProcess = spawn('python', [backendPath], {
			stdio: 'inherit',
			shell: true,
		});

		pythonProcess.on('error', (err) => {
			console.error('[Electron] Failed to start Python backend:', err);
		});

		pythonProcess.on('exit', (code) => {
			console.log(`[Electron] Python backend exited with code ${code}`);
		});
	});
}

function createWindow() {
	mainWindow = new BrowserWindow({
		width: 1280,
		height: 840,
		minWidth: 1024,
		minHeight: 700,
		backgroundColor: '#020617',
		title: 'SYRA — Autonomous PC Problem Resolver',
		webPreferences: {
			preload: path.join(__dirname, 'preload.cjs'),
			nodeIntegration: false,
			contextIsolation: true,
		},
		autoHideMenuBar: true,
	});

	if (isDev) {
		// In development: wait and load the Vite dev server
		const devUrl = 'http://127.0.0.1:5173';
		mainWindow.loadURL(devUrl).catch(() => {
			setTimeout(() => mainWindow.loadURL(devUrl), 2000);
		});
	} else {
		// In production: load built HTML
		mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
	}

	mainWindow.on('closed', () => {
		mainWindow = null;
	});
}

// IPC Handlers
ipcMain.on('window-minimize', () => {
	if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-maximize', () => {
	if (mainWindow) {
		if (mainWindow.isMaximized()) mainWindow.unmaximize();
		else mainWindow.maximize();
	}
});

ipcMain.on('window-close', () => {
	if (mainWindow) mainWindow.close();
});

ipcMain.on('desktop-notification', (_, { title, body }) => {
	if (Notification.isSupported()) {
		new Notification({
			title: title || 'SYRA PC Health Alert',
			body: body || 'System anomaly detected.',
		}).show();
	}
});

app.whenReady().then(() => {
	startBackend();
	createWindow();

	app.on('activate', () => {
		if (BrowserWindow.getAllWindows().length === 0) createWindow();
	});
});

app.on('window-all-closed', () => {
	if (pythonProcess) {
		pythonProcess.kill();
	}
	if (process.platform !== 'darwin') {
		app.quit();
	}
});

app.on('before-quit', () => {
	if (pythonProcess) {
		pythonProcess.kill();
	}
});
