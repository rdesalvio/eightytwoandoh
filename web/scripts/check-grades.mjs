// Full OUTCOME distribution (not just Cup%) vs the real draft mechanic, for three
// play styles, swept over anchor scales. Shows where rosters actually LAND on the
// playoff-round grade ladder so we can tune "challenging but not impossible".
import fs from 'fs';
const ds = JSON.parse(fs.readFileSync('./src/lib/data/players.json'));
const { pool, engine } = ds;
const { axes, weights, axisWeights, games, grades } = engine;

const byTD = new Map();
for (const pl of pool) { const k = pl.team + '|' + pl.decade; if (!byTD.has(k)) byTD.set(k, { F: [], D: [], G: [] }); byTD.get(k)[pl.grp].push(pl); }
for (const td of byTD.values()) for (const g of ['F', 'D', 'G']) td[g].sort((a, b) => b.overall - a.overall);
const keys = [...byTD.keys()].map((k) => k.split('|'));

const WEAK = Number(process.env.WEAK ?? engine.weakDiscount ?? 1); // discount on the single lowest axis (1 = off)
const teamAxes = (r) => { const o = {}; for (const k of axes) { let n = 0, d = 0; for (const pl of r) { const w = weights[pl.pos]?.[k] ?? 0; n += w * pl.axes[k]; d += w; } o[k] = d ? n / d : 0; } return o; };
const geomean = (o) => {
	let mk = null;
	for (const k of axes) { if ((axisWeights?.[k] ?? 1) <= 0) continue; if (mk === null || o[k] < o[mk]) mk = k; }
	let ls = 0, ws = 0;
	for (const k of axes) { let w = axisWeights?.[k] ?? 1; if (k === mk) w *= WEAK; ls += w * Math.log(Math.max(o[k], 1e-6)); ws += w; }
	return Math.exp(ls / ws);
};

function roll(open, taken) {
	const valid = keys.filter(([t, d]) => open.some((g) => byTD.get(t + '|' + d)[g].some((pl) => !taken.has(pl.id))));
	const wts = valid.map(([t, d]) => open.reduce((s, g) => s + byTD.get(t + '|' + d)[g].length, 0));
	let r = Math.random() * wts.reduce((a, b) => a + b, 0), i = 0;
	while (i < valid.length - 1 && (r -= wts[i]) > 0) i++;
	const [t, d] = valid[i];
	return byTD.get(t + '|' + d);
}
function bestOf(td, gs, taken) { const c = gs.flatMap((g) => td[g]).filter((pl) => !taken.has(pl.id)); return c.length ? c.reduce((a, b) => (b.overall > a.overall ? b : a)) : null; }
function draft(mode) {
	const roster = [], cnt = { F: 0, D: 0, G: 0 }, cap = { F: 3, D: 2, G: 1 }, taken = new Set(), meta = [];
	let guard = 0;
	while (roster.length < 6 && guard++ < 100) {
		const phase = cnt.F < 3 ? ['F'] : ['D', 'G'].filter((g) => cnt[g] < cap[g]);
		const td = roll(phase, taken);
		const cands = phase.flatMap((g) => td[g]).filter((pl) => !taken.has(pl.id));
		if (!cands.length) continue;
		const pl = mode === 'casual' ? cands[Math.floor(Math.random() * cands.length)] : cands.reduce((a, b) => (b.overall > a.overall ? b : a));
		roster.push(pl); cnt[pl.grp]++; taken.add(pl.id); meta.push({ pl, phase });
	}
	if (mode === 'rerolls') {
		const weak = [...meta.keys()].sort((a, b) => meta[a].pl.overall - meta[b].pl.overall).slice(0, 2);
		for (const i of weak) {
			const { pl, phase } = meta[i];
			const alt = bestOf(roll(phase, taken), [pl.grp], taken);
			if (alt && alt.overall > pl.overall) { taken.delete(pl.id); taken.add(alt.id); roster[roster.indexOf(pl)] = alt; meta[i] = { pl: alt, phase }; }
		}
	}
	return geomean(teamAxes(roster));
}

const top = (g, n) => pool.filter((p) => p.grp === g).sort((a, b) => b.overall - a.overall).slice(0, n);
const ceil = geomean(teamAxes([...top('F', 3), ...top('D', 2), ...top('G', 1)]));
const N = 12000, P = engine.p;
const S = { casual: [], skilled: [], rerolls: [] };
for (const m of Object.keys(S)) for (let i = 0; i < N; i++) S[m].push(draft(m));

const gradeOf = (w) => grades.find(([m]) => w >= m); // [minWins, code, label, color]
const ladder = grades.map((g) => g[2]); // labels high->low
const winsAt = (s, anchor) => Math.round(games * Math.min(1, s / anchor) ** P);

function hist(arr, anchor) {
	const counts = Object.fromEntries(ladder.map((l) => [l, 0]));
	let sum = 0;
	for (const s of arr) { const w = winsAt(s, anchor); counts[gradeOf(w)[2]]++; sum += w; }
	const med = arr.map((s) => winsAt(s, anchor)).sort((a, b) => a - b)[Math.floor(arr.length / 2)];
	return { counts, mean: (sum / arr.length).toFixed(1), med };
}

const scales = process.argv.slice(2).map(Number);
if (!scales.length) scales.push(engine.anchor / ceil); // default: current live scale
console.log(`ceiling=${ceil.toFixed(1)}  p=${P}  games=${games}  (current live anchor=${engine.anchor}, scale=${(engine.anchor / ceil).toFixed(3)})\n`);
for (const scale of scales) {
	const anchor = ceil * scale;
	console.log(`──────── ANCHOR_SCALE ${scale.toFixed(3)}  (anchor ${anchor.toFixed(1)}) ────────`);
	console.log(['mode'.padEnd(16), ...ladder.map((l) => l.slice(0, 11).padStart(12)), 'med'.padStart(5), 'mean'.padStart(6)].join(''));
	for (const m of Object.keys(S)) {
		const h = hist(S[m], anchor);
		const cells = ladder.map((l) => `${(100 * h.counts[l] / N).toFixed(0)}%`.padStart(12));
		console.log([m.padEnd(16), ...cells, String(h.med).padStart(5), String(h.mean).padStart(6)].join(''));
	}
	console.log('');
}
