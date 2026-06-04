/**
 * Layer-2 win engine. Team strength is a position-weighted MEAN per axis, then
 * the geometric mean across the five axes (so one weak axis caps you), mapped
 * through a convex curve anchored to the best achievable roster. Constants live
 * in the dataset's `engine` block (see pipeline/tune_curve.py).
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

export function geomean(axesObj, axes, weights = null) {
	let logsum = 0;
	let wsum = 0;
	for (const k of axes) {
		const w = weights?.[k] ?? 1;
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
	const axesObj = teamAxes(roster, engine);
	const strength = geomean(axesObj, engine.axes, engine.axisWeights);
	const ratio = Math.min(1, strength / engine.anchor);
	const exact = 82 * ratio ** engine.p;
	const wins = filled.length === 6 ? Math.round(exact) : Math.floor(exact);
	const losses = 82 - wins;

	let weakest = engine.axes[0];
	for (const k of engine.axes) if (axesObj[k] < axesObj[weakest]) weakest = k;

	return {
		axes: axesObj,
		strength,
		wins,
		losses,
		record: `${wins}-${losses}`,
		perfect: wins === 82,
		weakest,
		complete: filled.length === 6,
		...gradeFor(wins, engine.grades)
	};
}

/** Pretty axis labels for the UI. */
export const AXIS_LABELS = {
	scoring: 'Scoring',
	playmaking: 'Playmaking',
	twoway: 'Two-Way',
	goaltending: 'Goaltending',
	durability: 'Durability'
};
