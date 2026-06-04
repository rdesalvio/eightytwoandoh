<script>
	import { AXIS_LABELS } from '$lib/engine.js';

	let { axes, order, weakest = null, size = 260 } = $props();

	const pad = 42;
	const cx = size / 2;
	const cy = size / 2;
	const R = size / 2 - pad;

	function pt(i, frac) {
		const ang = -Math.PI / 2 + (i * 2 * Math.PI) / order.length;
		return [cx + R * frac * Math.cos(ang), cy + R * frac * Math.sin(ang)];
	}
	const rings = [0.25, 0.5, 0.75, 1];
	function ringPath(frac) {
		return order.map((_, i) => pt(i, frac).join(',')).join(' ');
	}
	let dataPath = $derived(order.map((k, i) => pt(i, Math.max(axes[k], 0) / 100).join(',')).join(' '));
</script>

<svg viewBox="0 0 {size} {size}" class="radar" role="img" aria-label="Team category ratings">
	{#each rings as r}
		<polygon points={ringPath(r)} class="ring" />
	{/each}
	{#each order as _, i}
		<line x1={cx} y1={cy} x2={pt(i, 1)[0]} y2={pt(i, 1)[1]} class="spoke" />
	{/each}
	<polygon points={dataPath} class="data" />
	{#each order as k, i}
		{@const [lx, ly] = pt(i, 1.22)}
		<text
			x={lx}
			y={ly}
			class="lbl"
			class:weak={k === weakest}
			text-anchor="middle"
			dominant-baseline="middle"
		>
			{AXIS_LABELS[k]}
		</text>
		<text x={lx} y={ly + 12} class="val" class:weak={k === weakest} text-anchor="middle">
			{Math.round(axes[k])}
		</text>
	{/each}
</svg>

<style>
	.radar {
		width: 100%;
		max-width: 312px;
		display: block;
		margin: 0 auto;
		overflow: visible;
	}
	.ring {
		fill: none;
		stroke: var(--line);
		stroke-width: 1;
	}
	.spoke {
		stroke: var(--line);
		stroke-width: 1;
	}
	.data {
		fill: color-mix(in srgb, var(--ice) 22%, transparent);
		stroke: var(--ice);
		stroke-width: 2;
		stroke-linejoin: round;
		filter: drop-shadow(0 0 6px rgba(232, 163, 61, 0.45));
	}
	.lbl {
		font-family: var(--display);
		font-size: 9.5px;
		font-weight: 700;
		fill: var(--ink-soft);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.val {
		font-family: var(--score);
		font-size: 14px;
		fill: var(--ink);
	}
	.lbl.weak,
	.val.weak {
		fill: var(--red-deep);
	}
</style>
