<script>
	let { roster, order } = $props();
	const shortName = (n) => {
		const parts = n.split(' ');
		return parts.length > 1 ? parts[0][0] + '. ' + parts.slice(1).join(' ') : n;
	};
</script>

<div class="bar">
	{#each order as grp, i (i)}
		{@const p = roster[i]}
		<div class="slot" class:filled={!!p}>
			<span class="pos {p ? p.pos : grp}">{p ? p.pos : grp}</span>
			{#if p}
				<span class="nm">{shortName(p.name)}</span>
				<span class="er">{p.team} · {p.decade}</span>
			{:else}
				<span class="nm empty">—</span>
				<span class="er">&nbsp;</span>
			{/if}
		</div>
	{/each}
</div>

<style>
	.bar {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0;
		border: 1px solid var(--line-2);
		border-top-color: var(--line-3);
		border-radius: 9px;
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0) 40%),
			linear-gradient(180deg, rgba(20, 50, 84, 0.5), rgba(8, 22, 40, 0.6));
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
		overflow: hidden;
	}
	.slot {
		padding: 8px 9px;
		min-height: 56px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
	}
	.slot:nth-child(3n) {
		border-right: none;
	}
	.slot:nth-child(n + 4) {
		border-bottom: none;
	}
	.slot.filled {
		background: linear-gradient(180deg, rgba(232, 163, 61, 0.14), rgba(232, 163, 61, 0));
		box-shadow: inset 2px 0 0 var(--amber);
	}
	.pos {
		align-self: flex-start;
	}
	.nm {
		font-size: 0.86rem;
		font-weight: 600;
		color: var(--ink);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.nm.empty {
		color: var(--faint);
	}
	.er {
		font-size: 0.66rem;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
	}
</style>
