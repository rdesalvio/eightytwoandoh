/**
 * Dataset loading, draft-roll indexing, seeded RNG (daily mode), theme filters,
 * and the share codec. The dataset is the single source of truth — engine
 * constants, teams, decades, and the player pool all come from players.json.
 */
import lzString from 'lz-string';
import dataset from './data/players.json';

export const { engine, teams, decades, meta } = dataset;
export const pool = dataset.pool;

export const SLOT_ORDER = ['F', 'F', 'F', 'D', 'D', 'G'];
export const GROUP_LABEL = { F: 'Forward', D: 'Defense', G: 'Goalie' };

// --- indexing -------------------------------------------------------------
/** "team|decade" -> { team, decade, F, D, G, groups } ; plus all roll keys. */
const byTD = new Map();
const allKeys = []; // [team, decade]
const stintIndex = new Map(); // "id|team|season" -> player (for share decode)

for (const p of pool) {
	const key = `${p.team}|${p.decade}`;
	let td = byTD.get(key);
	if (!td) {
		td = { team: p.team, decade: p.decade, F: [], D: [], G: [], groups: new Set() };
		byTD.set(key, td);
		allKeys.push([p.team, p.decade]);
	}
	td[p.grp].push(p);
	td.groups.add(p.grp);
	stintIndex.set(`${p.id}|${p.team}|${p.decade}`, p);
}
for (const td of byTD.values())
	for (const g of ['F', 'D', 'G']) td[g].sort((a, b) => b.overall - a.overall);

export function rollFromKey(team, decade, taken = null) {
	const td = byTD.get(`${team}|${decade}`);
	const f = (list) => (taken ? list.filter((p) => !taken.has(p.id)) : list);
	return { team, decade, teamName: teams[team] ?? team, F: f(td.F), D: f(td.D), G: f(td.G) };
}

// --- RNG ------------------------------------------------------------------
export function mulberry32(seed) {
	let a = seed >>> 0;
	return function () {
		a |= 0;
		a = (a + 0x6d2b79f5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

export function hashSeed(str) {
	let h = 1779033703 ^ str.length;
	for (let i = 0; i < str.length; i++) {
		h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
		h = (h << 13) | (h >>> 19);
	}
	return (h ^ (h >>> 16)) >>> 0;
}

/** UTC date key like "2026-06-03" for the daily challenge. */
export function todayKey(d = new Date()) {
	return d.toISOString().slice(0, 10);
}

// --- themes ---------------------------------------------------------------
const ORIGINAL_SIX = new Set(['MTL', 'TOR', 'BOS', 'NYR', 'CHI', 'DET']);
const O6_DECADES = new Set(['1940s', '1950s', '1960s']);
const DEAD_PUCK = new Set(['1990s', '2000s']);
const CAP_DECADES = new Set(['2000s', '2010s', '2020s']); // salary-cap era (2005-06+)

export const THEMES = [
	{ id: 'all', name: 'All-Time', blurb: 'The full sweep of NHL history, 1929-30 to today.' },
	{ id: 'original-six', name: 'Original Six', blurb: 'Just MTL, TOR, BOS, NYR, CHI, DET — the 1942-67 era.' },
	{ id: 'dead-puck', name: 'Dead Puck Era', blurb: 'The low-scoring clutch-and-grab 1990s–2000s.' },
	{ id: 'salary-cap', name: 'Salary Cap', blurb: 'The modern cap era — 2005-06 to today.' },
	{ id: 'decade', name: 'Single Decade', blurb: 'Lock the whole draft to one decade.' },
	{ id: 'franchise', name: 'One Franchise', blurb: 'Build entirely from a single team’s history.' }
];

/** Returns a filter predicate over a [team, decade] roll key for a theme. */
export function themeFilter(theme) {
	if (!theme || theme.id === 'all') return () => true;
	if (theme.id === 'original-six') return ([t, d]) => ORIGINAL_SIX.has(t) && O6_DECADES.has(d);
	if (theme.id === 'dead-puck') return ([, d]) => DEAD_PUCK.has(d);
	if (theme.id === 'salary-cap') return ([, d]) => CAP_DECADES.has(d);
	if (theme.id === 'decade') return ([, d]) => d === theme.value;
	if (theme.id === 'franchise') return ([t]) => t === theme.value;
	return () => true;
}

/**
 * Valid (team,decade) rolls under a theme that still hold at least one player in
 * one of the still-open position groups. `extra` optionally constrains the keys
 * (used for the franchise / era skips).
 */
export function validRollKeys(openGroups, theme, extra = null, taken = null) {
	const ok = themeFilter(theme);
	const keys = allKeys.filter((k) => {
		if (!ok(k)) return false;
		if (extra && !extra(k)) return false;
		const td = byTD.get(`${k[0]}|${k[1]}`);
		return openGroups.some((g) => td[g].some((p) => !taken || !taken.has(p.id)));
	});
	return keys;
}

/**
 * One slot-machine roll: a (team, decade) that can fill a still-open slot, with
 * every position's players attached (minus anyone already drafted). `rng` makes
 * the daily challenge reproducible.
 */
export function roll(openGroups, theme, rng = Math.random, extra = null, taken = null) {
	const keys = validRollKeys(openGroups, theme, extra, taken);
	if (!keys.length) return null;
	// Weight by how many eligible players the bucket holds for the open slots, so
	// deep, choice-rich team-eras come up far more than thin single-era expansion
	// fragments — keeps every spin interactive.
	const weights = keys.map(([t, d]) => {
		const td = byTD.get(`${t}|${d}`);
		let n = 0;
		for (const g of openGroups)
			for (const p of td[g]) if (!taken || !taken.has(p.id)) n++;
		return n;
	});
	let r = rng() * weights.reduce((a, b) => a + b, 0);
	let i = 0;
	while (i < keys.length - 1 && (r -= weights[i]) > 0) i++;
	const [team, decade] = keys[i];
	return rollFromKey(team, decade, taken);
}

// --- daily challenge ------------------------------------------------------
/** Valid (team,decade) keys (under a theme) that hold a player in EVERY group. */
export function validRollKeysAll(groups, theme) {
	const ok = themeFilter(theme);
	return allKeys.filter((k) => {
		if (!ok(k)) return false;
		const td = byTD.get(`${k[0]}|${k[1]}`);
		return groups.every((g) => td[g].length > 0);
	});
}

/** Seeded RNG for a daily/challenge — identical for everyone on a given key
 *  (defaults to today's UTC date). */
export function dailyRng(key) {
	return mulberry32(hashSeed('e82o|' + (key ?? todayKey())));
}

/** Today's themed constraint (seeded). Falls back to All-Time if a theme can't
 *  field a full roster. Consumes 1-2 draws from `rng`. */
export function pickDailyTheme(rng) {
	const r = rng();
	let theme;
	if (r < 0.3) theme = { id: 'all', name: 'All-Time' };
	else if (r < 0.44) theme = { id: 'original-six', name: 'Original Six' };
	else if (r < 0.56) theme = { id: 'dead-puck', name: 'Dead Puck Era' };
	else if (r < 0.68) theme = { id: 'salary-cap', name: 'Salary Cap Era' };
	else if (r < 0.84) {
		const d = decades[Math.floor(rng() * decades.length)];
		theme = { id: 'decade', value: d, name: `The ${d}` };
	} else {
		const storied = ['MTL', 'TOR', 'BOS', 'DET', 'CHI', 'NYR'];
		const t = storied[Math.floor(rng() * storied.length)];
		theme = { id: 'franchise', value: t, name: teams[t] ?? t };
	}
	if (validRollKeys(['F'], theme).length < 1 || validRollKeysAll(['D', 'G'], theme).length < 1)
		theme = { id: 'all', name: 'All-Time' };
	return theme;
}

function pickDistinct(keys, n, rng) {
	const pool = keys.slice();
	const out = [];
	for (let i = 0; i < n; i++) {
		if (!pool.length) out.push(keys[Math.floor(rng() * keys.length)]);
		else out.push(pool.splice(Math.floor(rng() * pool.length), 1)[0]);
	}
	return out;
}

/** A FIXED sequence of 6 rolls for the daily — identical for everyone, regardless
 *  of picks. Three forward team-eras, then three that each hold BOTH a D and a G
 *  so any pick order can finish 3F/2D/1G. */
export function buildDailyPlan(theme, rng) {
	const dgKeys = validRollKeysAll(['D', 'G'], theme);
	const fKeys = validRollKeys(['F'], theme);
	if (!dgKeys.length || !fKeys.length) return null;
	const dg = pickDistinct(dgKeys, 3, rng);
	const used = new Set(dg.map((k) => k[0] + '|' + k[1]));
	const fPool = fKeys.filter((k) => !used.has(k[0] + '|' + k[1]));
	const f = pickDistinct(fPool.length >= 3 ? fPool : fKeys, 3, rng);
	return [...f, ...dg].map(([t, d]) => rollFromKey(t, d));
}

// --- share codec ----------------------------------------------------------
/** Encode a finished roster + info-mode into a short URL-safe code. */
export function encodeRoster(roster, infoMode) {
	const payload = {
		m: infoMode === 'hockeyiq' ? 1 : 0,
		r: roster.filter(Boolean).map((p) => [p.id, p.team, p.decade])
	};
	return lzString.compressToEncodedURIComponent(JSON.stringify(payload));
}

/** Decode a share code back into { infoMode, roster }. Returns null if unusable. */
export function decodeRoster(code) {
	try {
		const json = lzString.decompressFromEncodedURIComponent(code);
		if (!json) return null;
		const { m, r } = JSON.parse(json);
		const roster = r.map(([id, team, decade]) => stintIndex.get(`${id}|${team}|${decade}`) ?? null);
		if (roster.some((p) => !p)) return null;
		return { infoMode: m ? 'hockeyiq' : 'classic', roster };
	} catch {
		return null;
	}
}
