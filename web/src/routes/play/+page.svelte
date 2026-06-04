<script>
	import { page } from '$app/state';
	import {
		teams,
		validRollKeys,
		roll,
		rollFromKey,
		mulberry32,
		hashSeed,
		todayKey,
		decodeRoster,
		encodeRoster
	} from '$lib/pool.js';
	import SlotMachine from '$lib/components/SlotMachine.svelte';
	import RosterBar from '$lib/components/RosterBar.svelte';
	import PlayerPick from '$lib/components/PlayerPick.svelte';
	import ResultView from '$lib/components/ResultView.svelte';

	const SLOT_ORDER = ['F', 'F', 'F', 'D', 'D', 'G'];
	const CAP = { F: 3, D: 2, G: 1 };

	// --- config from the URL --------------------------------------------------
	const sp = page.url.searchParams;
	const daily = sp.get('daily') === '1';
	const infoMode = daily ? 'classic' : sp.get('info') === 'hockeyiq' ? 'hockeyiq' : 'classic';
	const theme = daily ? { id: 'all' } : { id: sp.get('theme') || 'all', value: sp.get('value') || undefined };
	const dailyKey = `e82o-daily-${todayKey()}`;
	const rng = daily ? mulberry32(hashSeed('e82o|' + todayKey())) : Math.random;

	// --- state ----------------------------------------------------------------
	let roster = $state(Array(6).fill(null));
	let pickNum = $state(0);
	let phase = $state('spin'); // spin | pick | done
	let activeRoll = $state(null);
	let teaser = $state({ teamName: '—', decade: '' });
	let spinning = $state(false);
	let usedSkips = $state({ franchise: false, era: false });
	let alreadyPlayed = $state(false);

	const reduce =
		typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

	let openGroups = $derived(['F', 'D', 'G'].filter((g) => roster.filter((p) => p?.grp === g).length < CAP[g]));
	let taken = $derived(new Set(roster.filter(Boolean).map((p) => p.id)));
	const fr = (k) => activeRoll && k[1] === activeRoll.decade && k[0] !== activeRoll.team;
	const er = (k) => activeRoll && k[0] === activeRoll.team && k[1] !== activeRoll.decade;
	let canFranchise = $derived(!daily && !usedSkips.franchise && !!activeRoll && validRollKeys(openGroups, theme, fr, taken).length > 0);
	let canEra = $derived(!daily && !usedSkips.era && !!activeRoll && validRollKeys(openGroups, theme, er, taken).length > 0);

	// restore a finished daily run
	if (daily && typeof localStorage !== 'undefined') {
		const saved = localStorage.getItem(dailyKey);
		const dec = saved && decodeRoster(saved);
		if (dec) {
			roster = dec.roster;
			phase = 'done';
			alreadyPlayed = true;
		}
	}

	function spinTo(target) {
		if (!target) return;
		activeRoll = target;
		phase = 'spin';
		if (reduce) {
			teaser = { teamName: target.teamName, decade: target.decade };
			spinning = false;
			phase = 'pick';
			return;
		}
		spinning = true;
		const keys = validRollKeys(openGroups, theme);
		let n = 0;
		const iv = setInterval(() => {
			const [t, d] = keys[Math.floor(Math.random() * keys.length)] ?? [target.team, target.decade];
			teaser = { teamName: teams[t] ?? t, decade: d };
			if (++n > 9) {
				clearInterval(iv);
				teaser = { teamName: target.teamName, decade: target.decade };
				spinning = false;
				phase = 'pick';
			}
		}, 55);
	}

	function newSpin() {
		spinTo(roll(openGroups, theme, rng, null, taken));
	}

	function reroll(kind) {
		if (kind === 'franchise' ? !canFranchise : !canEra) return;
		usedSkips[kind] = true;
		spinTo(roll(openGroups, theme, rng, kind === 'franchise' ? fr : er, taken));
	}

	function pick(player) {
		const i = SLOT_ORDER.findIndex((g, idx) => g === player.grp && !roster[idx]);
		if (i < 0) return;
		roster[i] = player;
		if (++pickNum === 6) {
			phase = 'done';
			if (daily && typeof localStorage !== 'undefined')
				localStorage.setItem(dailyKey, encodeRoster(roster, infoMode));
		} else {
			newSpin();
		}
	}

	if (phase !== 'done') newSpin();
</script>

<svelte:head><title>Draft · Eighty-Two & Oh</title></svelte:head>

{#if phase === 'done'}
	{#if alreadyPlayed}
		<p class="chip" style="margin:0 auto 12px">Today’s daily — already played</p>
	{/if}
	<ResultView {roster} {infoMode} />
{:else}
	<div class="head">
		<a class="back" href="/" aria-label="Home">←</a>
		<div class="progress">
			<span class="eyebrow">{daily ? 'Daily' : infoMode === 'hockeyiq' ? 'Hockey-IQ' : 'Classic'}</span>
			<span class="rnd">Pick <b>{pickNum + 1}</b> <span class="faint">of 6</span></span>
		</div>
	</div>

	<RosterBar {roster} order={SLOT_ORDER} />

	<div class="machinewrap">
		<SlotMachine teamName={teaser.teamName} decade={teaser.decade} {spinning} />
	</div>

	{#if phase === 'pick'}
		{#if !daily}
			<div class="skips">
				<button class="btn sm ghost" disabled={!canFranchise} onclick={() => reroll('franchise')}>
					↻ New franchise{usedSkips.franchise ? ' ✓' : ''}
				</button>
				<button class="btn sm ghost" disabled={!canEra} onclick={() => reroll('era')}>
					↻ New era{usedSkips.era ? ' ✓' : ''}
				</button>
			</div>
		{/if}
		<PlayerPick roll={activeRoll} open={openGroups} {infoMode} onpick={pick} />
	{/if}
{/if}

<style>
	.head {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 12px;
	}
	.back {
		font-size: 1.5rem;
		color: var(--ink);
		border: none;
		line-height: 1;
	}
	.progress {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.rnd {
		font-family: var(--display);
		font-size: 1.15rem;
		letter-spacing: 0.02em;
	}
	.machinewrap {
		margin: 12px 0;
	}
	.skips {
		display: flex;
		gap: 8px;
		justify-content: center;
		margin-bottom: 12px;
	}
	.skips .btn {
		flex: 1;
	}
</style>
