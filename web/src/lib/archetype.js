/**
 * Auto-label a drafted player by their dominant trait, for the reveal screen.
 * Derived purely from the hidden axis ratings + position.
 */
export function archetype(p) {
	const a = p.axes;
	if (p.grp === 'G') {
		// goaltending is a percentile (phi99) across all goalie-eras, and the field
		// clusters high — a 75 is already the ~83rd percentile. Tiers track that so a
		// clear starter (top quartile) never reads as a "Backup".
		if (a.goaltending >= 90) return 'The Wall';
		if (a.goaltending >= 78) return 'Franchise Goalie';
		if (a.goaltending >= 60) return 'Steady Starter';
		if (a.goaltending >= 45) return 'Platoon Starter';
		return 'Backup';
	}
	if (p.grp === 'D') {
		// scoring is heavily compressed for D (only the rare puck-mover scores), so it
		// cleanly separates offensive blueliners; defense (twoway) then identifies the
		// shutdown/complete D so the elite two-way guys don't all read as "puck-movers".
		if (a.scoring >= 62) return 'Offensive D';
		if (a.twoway >= 92 || (a.twoway >= 86 && a.playmaking >= 84)) return 'Shutdown D';
		if (a.playmaking >= 64 || a.twoway >= 66) return 'Two-Way D';
		return 'Stay-at-Home D';
	}
	// forwards — judged on offense only (a forward's defense isn't measured here)
	if (a.scoring >= 94 && a.playmaking >= 93) return 'Franchise Forward';
	if (a.scoring - a.playmaking >= 11) return 'Sniper';
	if (a.playmaking - a.scoring >= 9) return 'Playmaker';
	if (a.scoring >= 78 || a.playmaking >= 78) return 'Scorer';
	return 'Depth Forward';
}
