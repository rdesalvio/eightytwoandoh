// Sweep anchor-scale x exponent against the REAL draft mechanic (1 weighted roll
// per slot, two-phase, best/random pick) to find a config with the target Cup rate.
import fs from 'fs';
const ds = JSON.parse(fs.readFileSync('./src/lib/data/players.json'));
const { pool, engine } = ds;
const { axes, weights, axisWeights, games, grades } = engine;

const byTD = new Map();
for (const pl of pool) {
	const k = pl.team + '|' + pl.decade;
	if (!byTD.has(k)) byTD.set(k, { F: [], D: [], G: [] });
	byTD.get(k)[pl.grp].push(pl);
}
for (const td of byTD.values()) for (const g of ['F', 'D', 'G']) td[g].sort((a, b) => b.overall - a.overall);
const keys = [...byTD.keys()].map((k) => k.split('|'));

const teamAxes = (r) => {
	const o = {};
	for (const k of axes) { let n = 0, d = 0; for (const pl of r) { const w = weights[pl.pos]?.[k] ?? 0; n += w * pl.axes[k]; d += w; } o[k] = d ? n / d : 0; }
	return o;
};
const geomean = (o) => { let ls = 0, ws = 0; for (const k of axes) { const w = axisWeights?.[k] ?? 1; ls += w * Math.log(Math.max(o[k], 1e-6)); ws += w; } return Math.exp(ls / ws); };
const gradeOf = (w) => grades.find(([m]) => w >= m)[1];

function roll(open) {
	const valid = keys.filter(([t, d]) => open.some((g) => byTD.get(t + '|' + d)[g].length));
	const wts = valid.map(([t, d]) => open.reduce((s, g) => s + byTD.get(t + '|' + d)[g].length, 0));
	let r = Math.random() * wts.reduce((a, b) => a + b, 0), i = 0;
	while (i < valid.length - 1 && (r -= wts[i]) > 0) i++;
	const [t, d] = valid[i];
	return byTD.get(t + '|' + d);
}
function draft(best) {
	const roster = [], cnt = { F: 0, D: 0, G: 0 }, cap = { F: 3, D: 2, G: 1 }, taken = new Set();
	let guard = 0;
	while (roster.length < 6 && guard++ < 100) {
		const phase = cnt.F < 3 ? ['F'] : ['D', 'G'].filter((g) => cnt[g] < cap[g]);
		const td = roll(phase);
		const cands = phase.flatMap((g) => td[g]).filter((pl) => !taken.has(pl.id));
		if (!cands.length) continue;
		const pl = best ? cands.reduce((a, b) => (b.overall > a.overall ? b : a)) : cands[Math.floor(Math.random() * cands.length)];
		roster.push(pl); cnt[pl.grp]++; taken.add(pl.id);
	}
	return roster;
}

// ceiling geomean (best achievable roster)
const top = (g, n) => pool.filter((p) => p.grp === g).sort((a, b) => b.overall - a.overall).slice(0, n);
const ceil = geomean(teamAxes([...top('F', 3), ...top('D', 2), ...top('G', 1)]));

const N = 15000;
const strengths = { casual: [], skilled: [] };
for (const best of [false, true]) for (let i = 0; i < N; i++) strengths[best ? 'skilled' : 'casual'].push(geomean(teamAxes(draft(best))));

console.log('ceiling geomean =', ceil.toFixed(1), '\n');
for (const scale of [0.925, 0.92, 0.915, 0.91, 0.905]) {
	const p = 2.5;
	const anchor = ceil * scale;
	for (const kind of ['casual', 'skilled']) {
		const hist = {}; let cup = 0;
		for (const s of strengths[kind]) { const w = Math.round(games * Math.min(1, s / anchor) ** p); hist[gradeOf(w)] = (hist[gradeOf(w)] || 0) + 1; if (w >= games) cup++; }
		const pct = grades.map((g) => g[1]).filter((g) => hist[g]).map((g) => `${g} ${(hist[g] / strengths[kind].length * 100).toFixed(0)}%`).join('  ');
		console.log(`scale ${scale} ${kind.padEnd(8)} Cup ${(cup / strengths[kind].length * 100).toFixed(1).padStart(4)}% | ${pct}`);
	}
}
