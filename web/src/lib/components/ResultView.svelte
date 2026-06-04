<script>
	import { engine, encodeRoster } from '$lib/pool.js';
	import { projectRecord, AXIS_LABELS } from '$lib/engine.js';
	import { archetype } from '$lib/archetype.js';
	import { renderShareCard } from '$lib/shareCard.js';
	import Radar from './Radar.svelte';
	import GradeBadge from './GradeBadge.svelte';
	import ShareBar from './ShareBar.svelte';

	let { roster, infoMode = 'classic', shared = false } = $props();

	let result = $derived(projectRecord(roster, engine));
	let origin = $state('');
	$effect(() => {
		origin = window.location.origin;
	});
	$effect(() => {
		if (import.meta.env.DEV) window.__shareCard = () => renderShareCard(result, roster);
	});

	let shareUrl = $derived(`${origin}/r/${encodeRoster(roster, infoMode)}`);
</script>

<div class="result fadeUp">
	<div class="card resultcard">
		<div class="masthead">
			<span class="rule"></span>
			<span class="brand chrome">Chase The Cup</span>
			<span class="rule"></span>
		</div>
		<GradeBadge {...result} />
		<Radar axes={result.axes} order={engine.axes} weakest={result.weakest} />
		<p class="weaknote">
			Weakest link:
			<b style="color:var(--red)">{AXIS_LABELS[result.weakest]}</b>{result.perfect
				? ''
				: ' — the category capping your record'}
		</p>
		<div class="roster">
			{#each roster as p, i (i)}
				<div class="pl">
					<span class="pos {p.pos}">{p.pos}</span>
					<div class="meta">
						<span class="nm">{p.name}</span>
						<span class="sub">{p.label}</span>
					</div>
					<span class="arch">{archetype(p)}</span>
					<span class="ovr">{p.overall}</span>
				</div>
			{/each}
		</div>
		<div class="foot">chase-the-cup.com — era-adjusted · all NHL history since 1929-30</div>
	</div>

	<div class="actions stack">
		<ShareBar url={shareUrl} makeImage={() => renderShareCard(result, roster)} />
		{#if shared}
			<a class="btn" href="/">🏒 Build your own six</a>
		{:else}
			<button class="btn ghost" onclick={() => location.reload()}>↻ Draft again</button>
			<a class="btn ghost" href="/">Home</a>
		{/if}
	</div>
</div>

<style>
	.result {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}
	.resultcard {
		padding: 16px 15px 12px;
		display: flex;
		flex-direction: column;
		gap: 11px;
	}
	.masthead {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.masthead .rule {
		flex: 1;
		height: 0;
		border-top: 1.5px solid var(--ink);
	}
	.brand {
		font-family: var(--display);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.84rem;
	}
	.weaknote {
		text-align: center;
		font-family: var(--serif);
		font-style: italic;
		font-size: 0.86rem;
		color: var(--ink-soft);
		margin: 0;
	}
	.roster {
		display: flex;
		flex-direction: column;
		border-top: 1.5px solid var(--ink);
		margin-top: 2px;
	}
	.pl {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 2px;
		border-bottom: 1px solid var(--line);
	}
	.meta {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
	}
	.nm {
		font-weight: 600;
		font-size: 0.94rem;
	}
	.sub {
		font-size: 0.7rem;
		color: var(--muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.arch {
		font-size: 0.62rem;
		font-weight: 700;
		color: var(--red-deep);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		text-align: right;
	}
	.ovr {
		font-family: var(--score);
		font-weight: 600;
		font-size: 1.6rem;
		line-height: 1;
		color: var(--amber-bright);
		min-width: 30px;
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.foot {
		text-align: center;
		font-size: 0.64rem;
		color: var(--faint);
		margin-top: 7px;
		letter-spacing: 0.02em;
	}
</style>
