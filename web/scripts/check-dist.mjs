// Sweep anchor-scale against the REAL mechanic, modeling THREE play styles:
//   casual  = 1 roll/slot, random pick, no re-rolls
//   skilled = 1 roll/slot, best available, no re-rolls
//   skilled+rerolls = best available, plus 2 re-rolls spent upgrading the 2
//                     weakest slots (the actual game gives 1 franchise + 1 era skip)
import fs from 'fs';
const ds = JSON.parse(fs.readFileSync('./src/lib/data/players.json'));
const { pool, engine } = ds;
const { axes, weights, axisWeights, games, grades } = engine;

const byTD = new Map();
for (const pl of pool) { const k = pl.team + '|' + pl.decade; if (!byTD.has(k)) byTD.set(k, { F: [], D: [], G: [] }); byTD.get(k)[pl.grp].push(pl); }
for (const td of byTD.values()) for (const g of ['F', 'D', 'G']) td[g].sort((a, b) => b.overall - a.overall);
const keys = [...byTD.keys()].map((k) => k.split('|'));

const teamAxes = (r) => { const o = {}; for (const k of axes) { let n = 0, d = 0; for (const pl of r) { const w = weights[pl.pos]?.[k] ?? 0; n += w * pl.axes[k]; d += w; } o[k] = d ? n / d : 0; } return o; };
const WEAK = Number(process.env.WEAK ?? engine.weakDiscount ?? 1);
const geomean = (o) => {
	let mk = null;
	for (const k of axes) { if ((axisWeights?.[k] ?? 1) <= 0) continue; if (mk === null || o[k] < o[mk]) mk = k; }
	let ls = 0, ws = 0;
	for (const k of axes) { let w = axisWeights?.[k] ?? 1; if (k === mk) w *= WEAK; ls += w * Math.log(Math.max(o[k], 1e-6)); ws += w; }
	return Math.exp(ls / ws);
};
const gradeOf = (w) => grades.find(([m]) => w >= m)[1];

function roll(open, taken) {
	const valid = keys.filter(([t, d]) => open.some((g) => byTD.get(t + '|' + d)[g].some((pl) => !taken.has(pl.id))));
	const wts = valid.map(([t, d]) => open.reduce((s, g) => s + byTD.get(t + '|' + d)[g].length, 0));
	let r = Math.random() * wts.reduce((a, b) => a + b, 0), i = 0;
	while (i < valid.length - 1 && (r -= wts[i]) > 0) i++;
	const [t, d] = valid[i];
	return byTD.get(t + '|' + d);
}
function bestOf(td, groups, taken) {
	const c = groups.flatMap((g) => td[g]).filter((pl) => !taken.has(pl.id));
	return c.length ? c.reduce((a, b) => (b.overall > a.overall ? b : a)) : null;
}
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
	return roster;
}

const top = (g, n) => pool.filter((p) => p.grp === g).sort((a, b) => b.overall - a.overall).slice(0, n);
const ceil = geomean(teamAxes([...top('F', 3), ...top('D', 2), ...top('G', 1)]));
const N = 15000;
const S = { casual: [], skilled: [], rerolls: [] };
for (const m of ['casual', 'skilled', 'rerolls']) for (let i = 0; i < N; i++) S[m].push(geomean(teamAxes(draft(m))));

const p = 2.5;
console.log('ceiling =', ceil.toFixed(1), 'p =', p, '\n');
for (const scale of [0.939, 0.938, 0.937, 0.936, 0.935, 0.934, 0.933]) {
	const anchor = ceil * scale;
	const cup = (arr) => (arr.filter((s) => Math.round(games * Math.min(1, s / anchor) ** p) >= games).length / arr.length * 100).toFixed(1);
	console.log(`scale ${scale}: Cup  casual ${cup(S.casual).padStart(4)}%   skilled ${cup(S.skilled).padStart(4)}%   skilled+rerolls ${cup(S.rerolls).padStart(4)}%`);
}
