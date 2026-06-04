<script>
	let { url, text, target } = $props();
	let copied = $state(false);
	let busy = $state(false);

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(url);
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			/* clipboard blocked — ignore */
		}
	}

	async function shareImage() {
		const node = typeof target === 'function' ? target() : target;
		if (!node || busy) return;
		busy = true;
		try {
			const { toBlob } = await import('html-to-image');
			const blob = await toBlob(node, { pixelRatio: 2, backgroundColor: '#0b1120' });
			if (!blob) return;
			const file = new File([blob], 'eightytwoandoh.png', { type: 'image/png' });
			if (navigator.canShare?.({ files: [file] })) {
				await navigator.share({ files: [file], text, url });
			} else {
				const a = document.createElement('a');
				a.href = URL.createObjectURL(blob);
				a.download = 'eightytwoandoh.png';
				a.click();
				URL.revokeObjectURL(a.href);
			}
		} catch {
			/* user cancelled or unsupported */
		} finally {
			busy = false;
		}
	}

	const enc = encodeURIComponent;
	let links = $derived({
		x: `https://twitter.com/intent/tweet?text=${enc(text)}&url=${enc(url)}`,
		bsky: `https://bsky.app/intent/compose?text=${enc(text + ' ' + url)}`,
		wa: `https://wa.me/?text=${enc(text + ' ' + url)}`
	});
</script>

<div class="share">
	<button class="btn primary" onclick={shareImage} disabled={busy}>
		{busy ? 'Rendering…' : '📸 Share as image'}
	</button>
	<div class="row">
		<button class="btn" onclick={copyLink}>{copied ? '✓ Copied link' : '🔗 Copy link'}</button>
	</div>
	<div class="socials">
		<a class="btn sm ghost" href={links.x} target="_blank" rel="noopener">X</a>
		<a class="btn sm ghost" href={links.bsky} target="_blank" rel="noopener">Bluesky</a>
		<a class="btn sm ghost" href={links.wa} target="_blank" rel="noopener">WhatsApp</a>
	</div>
</div>

<style>
	.share {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.socials {
		display: flex;
		gap: 8px;
		justify-content: center;
	}
	.socials .btn {
		flex: 1;
	}
</style>
