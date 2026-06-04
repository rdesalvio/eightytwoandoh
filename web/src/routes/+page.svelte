<script>
	import { goto } from '$app/navigation';
	import { teams, decades, meta } from '$lib/pool.js';

	let info = $state('classic');
	let theme = $state('all');
	let decade = $state(decades[decades.length - 2]);
	let franchise = $state('MTL');

	const teamOptions = $derived(
		Object.entries(teams)
			.map(([tri, name]) => ({ tri, name }))
			.sort((a, b) => a.name.localeCompare(b.name))
	);

	const THEME_CHIPS = [
		['all', 'All-Time'],
		['original-six', 'Original Six'],
		['dead-puck', 'Dead Puck'],
		['decade', 'Decade'],
		['franchise', 'Franchise']
	];

	function start() {
		const q = new URLSearchParams({ info, theme });
		if (theme === 'decade') q.set('value', decade);
		if (theme === 'franchise') q.set('value', franchise);
		goto(`/play?${q}`);
	}
	const daily = () => goto('/play?daily=1');
</script>

<header class="hero fadeUp">
	<div class="eyebrow">NHL · 1929–{String(meta.lastSeason).slice(4)} · era-adjusted</div>
	<h1>
		<span class="l1 chrome">Chase The</span>
		<span class="l2"><span class="cup">Cup</span></span>
	</h1>
	<div class="rule wm"></div>
	<p class="tag">
		Draft six legends from across hockey history. Ratings are <span class="serif-it">hidden</span> and
		era-adjusted — win all <b>16</b> and lift the Cup. Can you go <b>16-0</b>?
	</p>
</header>

<section class="card opts">
	<div class="field">
		<span class="flabel">Stats</span>
		<div class="seg">
			<button class:on={info === 'classic'} onclick={() => (info = 'classic')}>
				Classic<small>shown</small>
			</button>
			<button class:on={info === 'hockeyiq'} onclick={() => (info = 'hockeyiq')}>
				Hockey-IQ<small>hidden</small>
			</button>
		</div>
	</div>

	<div class="field">
		<span class="flabel">Pool</span>
		<div class="themes">
			{#each THEME_CHIPS as [id, label] (id)}
				<button class="tchip" class:on={theme === id} onclick={() => (theme = id)}>{label}</button>
			{/each}
		</div>
	</div>

	{#if theme === 'decade'}
		<select bind:value={decade} class="sel">
			{#each decades as d}<option value={d}>{d}</option>{/each}
		</select>
	{:else if theme === 'franchise'}
		<select bind:value={franchise} class="sel">
			{#each teamOptions as t}<option value={t.tri}>{t.name}</option>{/each}
		</select>
	{/if}

	<button class="btn primary big" onclick={start}>Start Draft →</button>
</section>

<button class="card daily" onclick={daily}>
	<div class="dleft">
		<div class="eyebrow gold">Daily Challenge</div>
		<div class="dtitle">Same draws for everyone today</div>
		<div class="muted dsub">One run · compare records</div>
	</div>
	<span class="darrow">→</span>
</button>

<a class="howto" href="/how-to-play">How to play &amp; how scoring works →</a>

<footer class="foot">
	Not affiliated with the NHL · stats from the public NHL API. Inspired by
	<a href="https://www.82-0.com" target="_blank" rel="noopener">82-0</a> &amp;
	<a href="https://www.20-0.com" target="_blank" rel="noopener">20-0</a>.
</footer>

<style>
	.hero {
		text-align: center;
		padding: 20px 4px 6px;
	}
	h1 {
		font-size: clamp(3.1rem, 18vw, 4.6rem);
		font-weight: 800;
		line-height: 0.86;
		margin-top: 8px;
		filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5));
	}
	.l1,
	.l2 {
		display: block;
	}
	.cup {
		color: var(--red);
		-webkit-text-fill-color: var(--red);
		text-shadow:
			-1px 0 rgba(70, 174, 191, 0.45),
			1px 0 rgba(255, 255, 255, 0.3);
	}
	.rule.wm {
		max-width: 230px;
		height: 3px;
		margin: 14px auto 0;
		border-radius: 2px;
		background: linear-gradient(90deg, transparent, var(--amber) 30%, var(--red) 70%, transparent);
		box-shadow: 0 0 12px rgba(232, 163, 61, 0.4);
	}
	.tag {
		color: var(--ink-soft);
		margin: 14px auto 0;
		max-width: 32ch;
		line-height: 1.5;
		font-size: 0.98rem;
	}
	.opts {
		padding: 15px;
		margin-top: 20px;
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 7px;
	}
	.flabel {
		font-family: var(--display);
		text-transform: uppercase;
		letter-spacing: 0.14em;
		font-size: 0.76rem;
		font-weight: 700;
		color: var(--ice);
	}
	.seg {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}
	.seg button {
		display: flex;
		flex-direction: column;
		gap: 1px;
		padding: 10px;
		border-radius: 7px;
		border: 1px solid var(--line);
		border-top-color: var(--line-2);
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 50%),
			rgba(255, 255, 255, 0.03);
		color: var(--ink-soft);
		font-family: var(--display);
		font-weight: 700;
		font-size: 1rem;
		text-transform: uppercase;
		cursor: pointer;
	}
	.seg button small {
		font-weight: 500;
		font-family: var(--body);
		font-size: 0.66rem;
		color: var(--faint);
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}
	.seg button.on {
		color: #fff;
		border-color: rgba(255, 255, 255, 0.3);
		border-top-color: rgba(255, 255, 255, 0.5);
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 48%),
			linear-gradient(180deg, #ff3a47, #c5141f);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
	}
	.seg button.on small {
		color: rgba(255, 255, 255, 0.8);
	}
	.themes {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}
	.tchip {
		padding: 7px 13px;
		border-radius: 6px;
		border: 1px solid var(--line);
		border-top-color: var(--line-2);
		background: rgba(255, 255, 255, 0.04);
		color: var(--ink-soft);
		font-family: var(--display);
		font-weight: 600;
		font-size: 0.86rem;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		cursor: pointer;
	}
	.tchip.on {
		color: #fff;
		border-color: rgba(255, 255, 255, 0.28);
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0) 50%),
			linear-gradient(180deg, #2f6fb0, #16467a);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
	}
	.sel {
		width: 100%;
		padding: 11px;
		border-radius: 7px;
		border: 1px solid var(--line-2);
		background: rgba(8, 22, 40, 0.7);
		color: var(--ink);
		font: inherit;
		font-weight: 600;
	}
	.big {
		padding: 14px;
		font-size: 1.1rem;
	}
	.daily {
		margin-top: 14px;
		padding: 15px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		cursor: pointer;
		text-align: left;
		width: 100%;
		color: var(--ink);
	}
	.dleft {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.eyebrow.gold {
		color: var(--gold);
	}
	.dtitle {
		font-family: var(--display);
		font-weight: 700;
		font-size: 1.2rem;
		text-transform: uppercase;
		letter-spacing: 0.01em;
	}
	.dsub {
		font-size: 0.78rem;
	}
	.darrow {
		font-family: var(--display);
		font-weight: 800;
		font-size: 1.9rem;
		color: var(--red-deep);
	}
	.howto {
		display: block;
		text-align: center;
		margin: 18px 0 6px;
		font-family: var(--display);
		font-weight: 600;
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		color: var(--ice);
	}
	.foot {
		text-align: center;
		font-size: 0.74rem;
		color: var(--muted);
		margin-top: auto;
		padding-top: 22px;
		line-height: 1.6;
	}
	.foot a {
		color: var(--red-deep);
	}
</style>
