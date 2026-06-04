<script>
	import { AXIS_LABELS } from '$lib/engine.js';

	// Canvas (not SVG) so html-to-image can rasterize it for share cards on
	// mobile Safari, where inline SVGs render black.
	let { axes, order, weakest = null, size = 300 } = $props();

	let canvas = $state();
	const DPR = 2;
	const COL = {
		grid: 'rgba(255,240,214,0.14)',
		fill: 'rgba(232,163,61,0.22)',
		line: '#e8a33d',
		lbl: '#cdbb98',
		val: '#f3e9d4',
		weak: '#ff5a4f'
	};

	function draw() {
		if (!canvas) return;
		const W = size;
		const cx = W / 2;
		const cy = W / 2;
		const R = W / 2 - 42;
		const n = order.length;
		canvas.width = W * DPR;
		canvas.height = W * DPR;
		const ctx = canvas.getContext('2d');
		ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
		ctx.clearRect(0, 0, W, W);

		const pt = (i, frac) => {
			const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
			return [cx + R * frac * Math.cos(a), cy + R * frac * Math.sin(a)];
		};
		const poly = (frac) => {
			ctx.beginPath();
			order.forEach((_, i) => {
				const [x, y] = pt(i, frac);
				i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
			});
			ctx.closePath();
		};

		// rings
		ctx.strokeStyle = COL.grid;
		ctx.lineWidth = 1;
		for (const fr of [0.25, 0.5, 0.75, 1]) {
			poly(fr);
			ctx.stroke();
		}
		// spokes
		order.forEach((_, i) => {
			const [x, y] = pt(i, 1);
			ctx.beginPath();
			ctx.moveTo(cx, cy);
			ctx.lineTo(x, y);
			ctx.stroke();
		});
		// data
		ctx.beginPath();
		order.forEach((k, i) => {
			const [x, y] = pt(i, Math.max(axes[k], 0) / 100);
			i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
		});
		ctx.closePath();
		ctx.fillStyle = COL.fill;
		ctx.fill();
		ctx.strokeStyle = COL.line;
		ctx.lineWidth = 2;
		ctx.lineJoin = 'round';
		ctx.shadowColor = 'rgba(232,163,61,0.55)';
		ctx.shadowBlur = 7;
		ctx.stroke();
		ctx.shadowBlur = 0;
		// labels + values
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		order.forEach((k, i) => {
			const [lx, ly] = pt(i, 1.17);
			const w = k === weakest;
			ctx.fillStyle = w ? COL.weak : COL.lbl;
			ctx.font = '700 10px "Saira Condensed", system-ui, sans-serif';
			ctx.fillText(AXIS_LABELS[k].toUpperCase(), lx, ly - 2);
			ctx.fillStyle = w ? COL.weak : COL.val;
			ctx.font = '600 16px "Teko", system-ui, sans-serif';
			ctx.fillText(Math.round(axes[k]), lx, ly + 12);
		});
	}

	$effect(() => {
		// touch reactive deps so it redraws on data change
		void (axes && order && weakest);
		draw();
	});
	$effect(() => {
		// redraw once webfonts are ready so labels aren't in a fallback face
		if (typeof document !== 'undefined' && document.fonts?.ready) {
			document.fonts.ready.then(draw);
		}
	});
</script>

<canvas bind:this={canvas} class="radar" aria-label="Team category ratings"></canvas>

<style>
	.radar {
		display: block;
		width: 100%;
		max-width: 300px;
		aspect-ratio: 1;
		margin: 0 auto;
	}
</style>
