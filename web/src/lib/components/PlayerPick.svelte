<script>
	let { roll, open, infoMode, onpick } = $props();

	const PLURAL = { F: 'Forwards', D: 'Defense', G: 'Goalies' };
	const groups = $derived(['F', 'D', 'G'].filter((g) => open.includes(g) && roll[g].length));

	function statline(p) {
		const s = p.stats;
		if (p.grp === 'G') {
			const sv = s.svp != null ? ` · .${String(Math.round(s.svp * 1000)).padStart(3, '0')} Sv%` : '';
			return `${s.w}W · ${s.gaa.toFixed(2)} GAA${sv} · ${s.so} SO`;
		}
		return `${s.g} G · ${s.a} A · ${s.p} P · ${s.gp} GP`;
	}
</script>

<div class="prompt">
	<span class="eyebrow">Take the best available</span>
	<span class="faint sub">slots fill as you pick</span>
</div>

{#each groups as g (g)}
	<div class="grp">
		<div class="ghead">
			<span class="pos {g}">{g}</span>
			<span class="gname">{PLURAL[g]}</span>
			<span class="gcount faint">{roll[g].length}</span>
		</div>
		<div class="list">
			{#each roll[g] as p, i (p.id + p.season)}
				<button class="pick" onclick={() => onpick(p)} style="animation-delay:{i * 28}ms">
					<span class="info">
						<span class="nm">{p.name}</span>
						<span class="sub2">
							{#if infoMode === 'classic'}{statline(p)}{:else}{p.label}{/if}
						</span>
					</span>
					<span class="go" aria-hidden="true">→</span>
				</button>
			{/each}
		</div>
	</div>
{/each}

<style>
	.prompt {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: 10px;
	}
	.sub {
		font-size: 0.72rem;
		font-style: italic;
		font-family: var(--serif);
	}
	.grp {
		margin-bottom: 16px;
	}
	.ghead {
		display: flex;
		align-items: center;
		gap: 8px;
		padding-bottom: 5px;
		margin-bottom: 6px;
		border-bottom: 1.5px solid var(--ink);
	}
	.gname {
		font-family: var(--display);
		font-size: 0.98rem;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
	.gcount {
		margin-left: auto;
		font-size: 0.74rem;
		font-variant-numeric: tabular-nums;
	}
	.list {
		display: flex;
		flex-direction: column;
	}
	.pick {
		display: flex;
		align-items: center;
		gap: 12px;
		width: 100%;
		text-align: left;
		padding: 9px 6px;
		border: none;
		border-bottom: 1px solid var(--line);
		background: transparent;
		color: var(--ink);
		cursor: pointer;
		font: inherit;
		animation: fadeUp 0.26s ease both;
	}
	.pick:hover {
		background: var(--paper-3);
	}
	.pick:active {
		background: var(--paper-3);
		transform: translateX(2px);
	}
	.info {
		display: flex;
		flex-direction: column;
		gap: 1px;
		flex: 1;
		min-width: 0;
	}
	.nm {
		font-weight: 600;
		font-size: 1rem;
	}
	.sub2 {
		font-size: 0.76rem;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
	}
	.go {
		color: var(--red);
		font-size: 1.1rem;
		font-weight: 700;
	}
	@keyframes fadeUp {
		from {
			opacity: 0;
			transform: translateY(5px);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
</style>
