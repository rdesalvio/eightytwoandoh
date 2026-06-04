<script>
	import { page } from '$app/state';
	import { decodeRoster } from '$lib/pool.js';
	import ResultView from '$lib/components/ResultView.svelte';

	const decoded = decodeRoster(page.params.code);
</script>

<svelte:head><title>A roster on Chase The Cup</title></svelte:head>

{#if decoded}
	<p class="eyebrow" style="text-align:center;margin-bottom:10px">Someone’s all-time six</p>
	<ResultView roster={decoded.roster} infoMode={decoded.infoMode} shared />
{:else}
	<div class="card bad">
		<h2>Hmm — couldn’t read that roster</h2>
		<p class="muted">The link may be incomplete or from an old version.</p>
		<a class="btn primary" href="/">Build your own six →</a>
	</div>
{/if}

<style>
	.bad {
		padding: 28px 20px;
		text-align: center;
		margin-top: 40px;
		display: flex;
		flex-direction: column;
		gap: 14px;
		align-items: center;
	}
</style>
