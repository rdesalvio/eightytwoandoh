// Print a few sample WINNING rosters from skilled Classic (all-time) drafts.
import fs from 'fs';
const ds = JSON.parse(fs.readFileSync('./src/lib/data/players.json'));
const { pool, engine } = ds;
const { axes, weights, axisWeights, anchor, p, games, grades } = engine;

const byTD = new Map();
for (const pl of pool) {
	const k = pl.team + '|' + pl.decade;
	if (!byTD.has(k)) byTD.set(k, { F: [], D: [], G: [] });
	byTD.get(k)[pl.grp].push(pl);
}
for (const td of byTD.values()) for (const g of ['F', 'D', 'G']) td[g].sort((a, b) => b.overall - a.overall);
const keys = [...byTD.keys()].map((k) => k.split('|'));

const teamAxes = (r) => { const o = {}; for (const k of axes) { let n = 0, d = 0; for (const pl of r) { const w = weights[pl.pos]?.[k] ?? 0; n += w * pl.axes[k]; d += w; } o[k] = d ? n / d : 0; } return o; };
const geomean = (o) => { let ls = 0, ws = 0; for (const k of axes) { const w = axisWeights?.[k] ?? 1; ls += w * Math.log(Math.max(o[k], 1e-6)); ws += w; } return Math.exp(ls / ws); };
const winsOf = (r) => Math.round(games * Math.min(1, geomean(teamAxes(r)) / anchor) ** p);
const grAt = (w) => grades.find(([m]) => w >= m);

function roll(open, taken) {
	const valid = keys.filter(([t, d]) => open.some((g) => byTD.get(t + '|' + d)[g].some((pl) => !taken.has(pl.id))));
	const wts = valid.map(([t, d]) => open.reduce((s, g) => s + byTD.get(t + '|' + d)[g].length, 0));
	let r = Math.random() * wts.reduce((a, b) => a + b, 0), i = 0;
	while (i < valid.length - 1 && (r -= wts[i]) > 0) i++;
	const [t, d] = valid[i];
	return byTD.get(t + '|' + d);
}
function draft() {
	const roster = [], cnt = { F: 0, D: 0, G: 0 }, cap = { F: 3, D: 2, G: 1 }, taken = new Set();
	const order = ['F', 'F', 'F', 'D', 'D', 'G'];
	let guard = 0;
	while (roster.length < 6 && guard++ < 100) {
		const phase = cnt.F < 3 ? ['F'] : ['D', 'G'].filter((g) => cnt[g] < cap[g]);
		const td = roll(phase, taken);
		const cands = phase.flatMap((g) => td[g]).filter((pl) => !taken.has(pl.id));
		if (!cands.length) continue;
		const pl = cands.reduce((a, b) => (b.overall > a.overall ? b : a)); // skilled = best available
		roster.push(pl); cnt[pl.grp]++; taken.add(pl.id);
	}
	return order.map((g) => roster.find((p, i) => p.grp === g && roster.indexOf(p) === roster.findIndex((q) => q.grp === g && !roster.slice(0, roster.indexOf(q)).includes(q)))) && roster;
}

const TARGET = Number(process.argv[3] ?? 16); // min wins to show (16 = Cup Champions)
const seen = new Set();
const winners = [];
for (let i = 0; i < 60000 && winners.length < 5; i++) {
	const r = draft();
	if (r.length !== 6) continue;
	const w = winsOf(r);
	const [, grade] = grAt(w);
	if (w < TARGET) continue;
	const key = r.map((p) => p.id).sort().join(',');
	if (seen.has(key)) continue;
	seen.add(key);
	winners.push({ r, w, grade });
}

for (const { r, w, grade } of winners) {
	const [, , label] = grAt(w);
	console.log(`\n${w}-${games - w}  (${grade} · ${label})`);
	const slot = (g) => r.filter((p) => p.grp === g);
	for (const p of [...slot('F'), ...slot('D'), ...slot('G')])
		console.log(`  ${p.pos.padEnd(2)} ${p.name.padEnd(20)} ${p.label.padEnd(28)} ${String(p.overall).padStart(2)}`);
}
