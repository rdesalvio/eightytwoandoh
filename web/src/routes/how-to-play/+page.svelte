<script>
	import { engine, meta } from '$lib/pool.js';
	const grades = engine.grades;
	const CATS = [
		['Scoring', 'Goals', 'Forwards'],
		['Playmaking', 'Assists', 'Forwards & puck-moving D'],
		['Defense', 'Your defensemen vs their peers', 'Defensemen'],
		['Goaltending', 'Goalie quality vs his era', 'Your goalie'],
		['Durability', 'Games played & longevity', 'Everyone · counts least']
	];
</script>

<svelte:head><title>How to play · Chase The Cup</title></svelte:head>

<header class="h">
	<a class="back" href="/" aria-label="Home">←</a>
	<h1>How to play</h1>
</header>

<section class="card sec">
	<h2>The goal</h2>
	<p>
		Draft six players from across NHL history — <b>3 forwards, 2 defensemen, 1 goalie</b> — and an
		engine projects your run through the playoffs: <b>16 wins</b> (four rounds of four) lift the
		Stanley Cup. A perfect <b>16-0</b> sweep is the dream.
	</p>
</section>

<section class="card sec">
	<h2>The draft</h2>
	<p>
		Each of your six picks starts with a <b>slot-machine roll</b> that lands on a franchise and an
		era, then shows you every player it has — forwards, defense, goalies. Take one; it drops into a
		matching slot and the choices narrow as you fill up. Stuck with a weak roll? You get
		<b>two skips</b> per game — one to re-roll the franchise, one to re-roll the era.
	</p>
</section>

<section class="card sec">
	<h2>How scoring works</h2>
	<p>
		Every player is scored <b>0–99 in each of five categories</b>, measured only against others from
		<span class="serif-it">their own era</span> — so a 1950s great isn’t punished for low modern
		totals. That rating is <b>hidden</b>; infer it from the stats, the year, and your hockey sense.
	</p>
	<div class="cats">
		<div class="crow chead">
			<span>Category</span><span>Built from</span><span>Driven by</span>
		</div>
		{#each CATS as [name, from, who]}
			<div class="crow">
				<span class="cname">{name}</span><span>{from}</span><span class="cwho">{who}</span>
			</div>
		{/each}
	</div>
	<p class="note">
		Each group is judged on its own job — forwards on Scoring &amp; Playmaking, your two
		defensemen on Defense, your goalie on Goaltending; everyone shares Durability. Your record
		blends all five and your <b>lowest</b> drags hardest, so chase <b>balance</b>, not just scoring.
		(Durability is weighted lightest — a fun bonus, not the main event.)
	</p>
</section>

<section class="card sec">
	<h2>Why it starts in 1929-30</h2>
	<p>
		Forward passing wasn’t legal in the attacking zone until <b>1929-30</b> — the season scoring
		nearly tripled and hockey first looked like the modern game. Everything before is a different
		sport that can’t be fairly era-adjusted, so the player pool begins there.
	</p>
</section>

<section class="card sec">
	<h2>Modes</h2>
	<ul class="modes">
		<li><b>Classic</b> — full stat lines shown while you draft.</li>
		<li><b>Hockey-IQ</b> — stats hidden. Draft from memory and knowledge alone.</li>
		<li><b>Daily Challenge</b> — everyone gets the same draws today. One run, compare records.</li>
		<li><b>Themed drafts</b> — Original Six, the Dead Puck era, a single decade, or one franchise.</li>
	</ul>
</section>

<section class="card sec">
	<h2>Grades</h2>
	<div class="grades">
		{#each grades as [min, g, label, color]}
			<div class="gr">
				<span class="g" style="color:{color};border-color:{color}">{g}</span>
				<span class="gl">{label}</span>
				<span class="gw muted">{g === 'S+' ? '16-0' : min + '+ W'}</span>
			</div>
		{/each}
	</div>
</section>

<a class="btn primary" href="/" style="margin:6px 0 26px;border-bottom:none">Build your six →</a>

<style>
	.h {
		display: flex;
		align-items: center;
		gap: 12px;
		margin: 10px 0 16px;
	}
	.back {
		font-size: 1.5rem;
		color: var(--ink);
		border: none;
	}
	h1 {
		font-size: 2rem;
	}
	.sec {
		padding: 15px;
		margin-bottom: 12px;
	}
	.sec h2 {
		font-size: 1.15rem;
		margin-bottom: 8px;
		color: var(--red);
	}
	.sec p {
		margin: 0;
		line-height: 1.58;
		font-size: 0.92rem;
	}
	.cats {
		margin: 12px 0;
		border-top: 1.5px solid var(--ink);
	}
	.crow {
		display: grid;
		grid-template-columns: 0.9fr 1fr 1.1fr;
		gap: 8px;
		padding: 7px 0;
		border-bottom: 1px solid var(--line);
		font-size: 0.82rem;
		align-items: baseline;
	}
	.chead {
		font-family: var(--display);
		text-transform: uppercase;
		font-size: 0.68rem;
		letter-spacing: 0.06em;
		color: var(--muted);
	}
	.cname {
		font-weight: 700;
	}
	.cwho {
		color: var(--ink-soft);
	}
	.note {
		font-size: 0.88rem !important;
		color: var(--ink-soft);
	}
	.modes {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.modes li {
		font-size: 0.9rem;
		line-height: 1.5;
		padding-left: 12px;
		border-left: 2px solid var(--red);
	}
	.grades {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}
	.gr {
		min-width: 84px;
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 3px;
		padding: 9px 6px;
		border: 1.5px solid var(--ink);
		border-radius: 2px;
		background: var(--paper);
	}
	.g {
		font-family: var(--display);
		font-size: 1.15rem;
		border: 2px solid;
		border-radius: 3px;
		padding: 0 8px;
	}
	.gl {
		font-size: 0.72rem;
		font-weight: 700;
		text-align: center;
	}
	.gw {
		font-size: 0.66rem;
		font-variant-numeric: tabular-nums;
	}
</style>
