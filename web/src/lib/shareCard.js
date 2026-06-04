/**
 * Draw the shareable result card entirely on a <canvas> and export a PNG blob.
 * We do NOT screenshot the DOM (html-to-image renders SVG/canvas black on mobile
 * Safari) — drawing on a canvas is reliable on every device.
 */
import { AXIS_LABELS } from './engine.js';

const W = 1080;
const H = 1350;
const ORDER = ['scoring', 'playmaking', 'twoway', 'goaltending', 'durability'];
const C = {
	cream: '#f3e9d4',
	muted: '#a4906f',
	faint: '#80714f',
	red: '#e4212f',
	amber: '#e8a33d',
	line: 'rgba(255,240,214,0.16)'
};
const D = '"Saira Condensed", system-ui, sans-serif';
const N = '"Teko", system-ui, sans-serif';
const B = '"Barlow Semi Condensed", system-ui, sans-serif';

function rr(ctx, x, y, w, h, r) {
	ctx.beginPath();
	ctx.moveTo(x + r, y);
	ctx.arcTo(x + w, y, x + w, y + h, r);
	ctx.arcTo(x + w, y + h, x, y + h, r);
	ctx.arcTo(x, y + h, x, y, r);
	ctx.arcTo(x, y, x + w, y, r);
	ctx.closePath();
}

function drawRadar(ctx, cx, cy, R, axes, weakest) {
	const n = ORDER.length;
	const pt = (i, f) => {
		const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
		return [cx + R * f * Math.cos(a), cy + R * f * Math.sin(a)];
	};
	const poly = (f) => {
		ctx.beginPath();
		ORDER.forEach((_, i) => {
			const [x, y] = pt(i, f);
			i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
		});
		ctx.closePath();
	};
	ctx.strokeStyle = C.line;
	ctx.lineWidth = 1.5;
	for (const f of [0.25, 0.5, 0.75, 1]) {
		poly(f);
		ctx.stroke();
	}
	ORDER.forEach((_, i) => {
		const [x, y] = pt(i, 1);
		ctx.beginPath();
		ctx.moveTo(cx, cy);
		ctx.lineTo(x, y);
		ctx.stroke();
	});
	ctx.beginPath();
	ORDER.forEach((k, i) => {
		const [x, y] = pt(i, Math.max(axes[k], 0) / 100);
		i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
	});
	ctx.closePath();
	ctx.fillStyle = 'rgba(232,163,61,0.26)';
	ctx.fill();
	ctx.strokeStyle = C.amber;
	ctx.lineWidth = 3;
	ctx.lineJoin = 'round';
	ctx.stroke();

	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	ORDER.forEach((k, i) => {
		const [lx, ly] = pt(i, 1.2);
		const w = k === weakest;
		ctx.fillStyle = w ? C.red : C.muted;
		ctx.font = `700 19px ${D}`;
		ctx.fillText(AXIS_LABELS[k].toUpperCase(), lx, ly - 6);
		ctx.fillStyle = w ? C.red : C.cream;
		ctx.font = `600 34px ${N}`;
		ctx.fillText(Math.round(axes[k]), lx, ly + 20);
	});
	ctx.textBaseline = 'alphabetic';
}

function posColors(grp) {
	if (grp === 'G') return ['#ff6e68', '#e0151f', '#fff'];
	if (grp === 'D') return ['#ffdb82', '#f0a528', '#07121f'];
	return ['#9be4ff', '#34a9e8', '#07121f'];
}

export async function renderShareCard(result, roster) {
	const canvas = document.createElement('canvas');
	canvas.width = W;
	canvas.height = H;
	const ctx = canvas.getContext('2d');

	try {
		await document.fonts.ready;
		await Promise.all([
			document.fonts.load(`700 44px "Saira Condensed"`),
			document.fonts.load(`800 46px "Saira Condensed"`),
			document.fonts.load(`600 220px "Teko"`),
			document.fonts.load(`600 30px "Barlow Semi Condensed"`)
		]);
	} catch {
		/* fonts already there or unsupported — fall back to system */
	}

	// background
	const g = ctx.createLinearGradient(0, 0, 0, H);
	g.addColorStop(0, '#15324b');
	g.addColorStop(0.5, '#0e2235');
	g.addColorStop(1, '#0a1626');
	ctx.fillStyle = g;
	ctx.fillRect(0, 0, W, H);
	const rg = ctx.createRadialGradient(W / 2, -120, 60, W / 2, -120, 760);
	rg.addColorStop(0, 'rgba(232,163,61,0.2)');
	rg.addColorStop(1, 'rgba(232,163,61,0)');
	ctx.fillStyle = rg;
	ctx.fillRect(0, 0, W, 560);
	ctx.fillStyle = 'rgba(255,240,214,0.04)';
	ctx.fillRect(40, 40, W - 80, H - 80);

	// header
	ctx.textAlign = 'center';
	ctx.fillStyle = C.cream;
	ctx.font = `700 46px ${D}`;
	if ('letterSpacing' in ctx) ctx.letterSpacing = '6px';
	ctx.fillText('CHASE THE CUP', W / 2, 100);
	if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
	ctx.strokeStyle = C.line;
	ctx.lineWidth = 2;
	ctx.beginPath();
	ctx.moveTo(W / 2 - 210, 128);
	ctx.lineTo(W / 2 + 210, 128);
	ctx.stroke();

	// record
	ctx.fillStyle = result.perfect ? C.amber : C.cream;
	ctx.font = `600 230px ${N}`;
	ctx.fillText(result.record, W / 2, 350);
	ctx.fillStyle = C.red;
	rr(ctx, W / 2 - 95, 376, 190, 7, 4);
	ctx.fill();

	// grade chip + label
	const gc = result.color;
	const label = result.label.toUpperCase();
	ctx.font = `800 48px ${D}`;
	const chipW = ctx.measureText(result.grade).width + 36;
	ctx.font = `700 38px ${D}`;
	const labelW = ctx.measureText(label).width;
	const gap = 26;
	let gx = (W - (chipW + gap + labelW)) / 2;
	const gy = 470;
	ctx.strokeStyle = gc;
	ctx.lineWidth = 3;
	rr(ctx, gx, gy - 44, chipW, 60, 9);
	ctx.stroke();
	ctx.fillStyle = gc;
	ctx.textAlign = 'center';
	ctx.font = `800 48px ${D}`;
	ctx.fillText(result.grade, gx + chipW / 2, gy);
	ctx.textAlign = 'left';
	ctx.font = `700 38px ${D}`;
	ctx.fillText(label, gx + chipW + gap, gy - 3);

	// radar
	drawRadar(ctx, W / 2, 745, 192, result.axes, result.weakest);

	// weakest note
	ctx.textAlign = 'center';
	ctx.fillStyle = C.muted;
	ctx.font = `italic 600 30px ${B}`;
	ctx.fillText(`Weakest link: ${AXIS_LABELS[result.weakest]}`, W / 2, 992);

	// roster
	let y = 1018;
	const x = 70;
	const rw = W - 140;
	for (const p of roster) {
		ctx.strokeStyle = C.line;
		ctx.lineWidth = 1;
		ctx.beginPath();
		ctx.moveTo(x, y + 48);
		ctx.lineTo(x + rw, y + 48);
		ctx.stroke();
		const [c0, c1, tc] = posColors(p.grp);
		const bg = ctx.createLinearGradient(x, y, x, y + 40);
		bg.addColorStop(0, c0);
		bg.addColorStop(1, c1);
		ctx.fillStyle = bg;
		rr(ctx, x, y + 4, 40, 38, 6);
		ctx.fill();
		ctx.fillStyle = tc;
		ctx.textAlign = 'center';
		ctx.font = `800 24px ${D}`;
		ctx.fillText(p.pos, x + 20, y + 31);
		ctx.textAlign = 'left';
		ctx.fillStyle = C.cream;
		ctx.font = `600 31px ${B}`;
		ctx.fillText(p.name, x + 54, y + 22);
		ctx.fillStyle = C.muted;
		ctx.font = `400 21px ${B}`;
		ctx.fillText(p.label, x + 54, y + 44);
		ctx.textAlign = 'right';
		ctx.fillStyle = C.amber;
		ctx.font = `600 46px ${N}`;
		ctx.fillText(p.overall, x + rw, y + 40);
		y += 50;
	}

	// footer
	ctx.textAlign = 'center';
	ctx.fillStyle = C.faint;
	ctx.font = `600 26px ${D}`;
	ctx.fillText('chase-the-cup.com', W / 2, H - 34);

	return await new Promise((res) => canvas.toBlob(res, 'image/png'));
}
