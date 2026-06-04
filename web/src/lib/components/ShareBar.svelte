<script>
	let { url, makeImage } = $props();
	let copied = $state(false);
	let busy = $state(false);

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(url);
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			/* clipboard blocked */
		}
	}

	// Link share, no text — the link's own preview card does the talking.
	async function shareLink() {
		if (navigator.share) {
			try {
				await navigator.share({ title: 'Chase The Cup', url });
				return;
			} catch {
				/* cancelled */
				return;
			}
		}
		copyLink();
	}

	// Image + link (no text blurb).
	async function shareImage() {
		if (busy) return;
		busy = true;
		try {
			const blob = await makeImage();
			if (!blob) return;
			const file = new File([blob], 'chase-the-cup.png', { type: 'image/png' });
			if (navigator.canShare?.({ files: [file] })) {
				await navigator.share({ files: [file], url });
			} else {
				const a = document.createElement('a');
				a.href = URL.createObjectURL(blob);
				a.download = 'chase-the-cup.png';
				a.click();
				URL.revokeObjectURL(a.href);
			}
		} catch {
			/* cancelled / unsupported */
		} finally {
			busy = false;
		}
	}

	const enc = encodeURIComponent;
	// link-only social intents (no text)
	let links = $derived({
		x: `https://twitter.com/intent/tweet?url=${enc(url)}`,
		bsky: `https://bsky.app/intent/compose?text=${enc(url)}`,
		wa: `https://wa.me/?text=${enc(url)}`
	});
</script>

<div class="share">
	<button class="btn primary" onclick={shareImage} disabled={busy}>
		{busy ? 'Rendering…' : '📸 Share image'}
	</button>
	<div class="row">
		<button class="btn" onclick={shareLink}>🔗 Share link</button>
		<button class="btn" onclick={copyLink}>{copied ? '✓ Copied' : 'Copy'}</button>
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
	.row .btn {
		flex: 1;
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
