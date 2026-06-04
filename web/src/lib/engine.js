/**
 * Layer-2 win engine. Team strength is a position-weighted MEAN per axis, then
 * the geometric mean across the four axes (so a weak axis caps you) — with the
 * single lowest axis discounted (engine.weakDiscount) so your stars cover for your
 * one worst category. Mapped through a convex curve anchored to the best achievable
 * roster. Constants live in the dataset's `engine` block (see pipeline/build_dataset.py).
 */

/** Position-weighted mean of each axis across the filled roster. */
export function teamAxes(roster, engine) {
	const { axes, weights } = engine;
	const out = {};
	for (const k of axes) {
		let num = 0;
		let den = 0;
		for (const pl of roster) {
			if (!pl) continue;
			const w = weights[pl.pos]?.[k] ?? 0;
			num += w * pl.axes[k];
			den += w;
		}
		out[k] = den ? num / den : 0;
	}
	return out;
}

export function geomean(axesObj, axes, weights = null, weakDiscount = 1) {
	// the single lowest full-weight axis is discounted — "your stars cover for your
	// one worst category" — softening the one-weak-link cap for near-complete rosters.
	let minK = null;
	if (weakDiscount !== 1) {
		for (const k of axes) {
			if ((weights?.[k] ?? 1) <= 0) continue;
			if (minK === null || axesObj[k] < axesObj[minK]) minK = k;
		}
	}
	let logsum = 0;
	let wsum = 0;
	for (const k of axes) {
		let w = weights?.[k] ?? 1;
		if (k === minK) w *= weakDiscount;
		logsum += w * Math.log(Math.max(axesObj[k], 1e-6));
		wsum += w;
	}
	return Math.exp(logsum / wsum);
}

export function gradeFor(wins, grades) {
	for (const [minWins, grade, label, color] of grades) {
		if (wins >= minWins) return { grade, label, color };
	}
	const last = grades[grades.length - 1];
	return { grade: last[1], label: last[2], color: last[3] };
}

/**
 * Project an 82-game record for a roster (any subset of the 6 slots filled).
 * Returns the per-axis team values, the overall strength, projected wins/losses,
 * the grade, and which axis is weakest (the one capping you).
 */
export function projectRecord(roster, engine) {
	const filled = roster.filter(Boolean);
	const games = engine.games ?? 16;
	const axesObj = teamAxes(roster, engine);
	const strength = geomean(axesObj, engine.axes, engine.axisWeights, engine.weakDiscount ?? 1);
	const ratio = Math.min(1, strength / engine.anchor);
	const exact = games * ratio ** engine.p;
	const wins = filled.length === 6 ? Math.round(exact) : Math.floor(exact);
	const losses = games - wins;

	// "weakest link" = lowest of the full-weight axes only; durability is a
	// downweighted bonus, so it shouldn't keep getting flagged as the cap.
	let weakest = null;
	for (const k of engine.axes) {
		if ((engine.axisWeights?.[k] ?? 1) < 1) continue;
		if (weakest === null || axesObj[k] < axesObj[weakest]) weakest = k;
	}

	return {
		axes: axesObj,
		strength,
		wins,
		losses,
		record: `${wins}-${losses}`,
		perfect: wins === games,
		weakest,
		complete: filled.length === 6,
		...gradeFor(wins, engine.grades)
	};
}

/** Pretty axis labels for the UI. */
export const AXIS_LABELS = {
	scoring: 'Scoring',
	playmaking: 'Playmaking',
	twoway: 'Defense',
	goaltending: 'Goaltending',
	durability: 'Durability'
};
