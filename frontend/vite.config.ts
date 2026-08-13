import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	base: './',
	plugins: [react(), tailwindcss()],
	server: {
		port: 5173,
		strictPort: true,
		host: '0.0.0.0',
		proxy: {
			'/api': {
				target: process.env.SYRA_API_URL || 'http://127.0.0.1:8000',
				changeOrigin: true,
			},
		},
	},
	build: {
		outDir: 'dist',
	},
});
