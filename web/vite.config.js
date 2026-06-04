import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// allow previewing the dev server through a cloudflared quick tunnel
		allowedHosts: ['.trycloudflare.com']
	}
});
