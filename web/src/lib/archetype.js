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
		if (a.scoring >= 85 || a.playmaking >= 90) return 'Puck-Mover';
		if (a.twoway >= 85) return 'Shutdown D';
		return 'Two-Way D';
	}
	// forwards — valued on offense, never judged on "defense"
	if (a.scoring >= 88 && a.playmaking >= 88) return 'Superstar';
	if (a.scoring - a.playmaking >= 12) return 'Sniper';
	if (a.playmaking - a.scoring >= 12) return 'Playmaker';
	if (a.durability >= 88) return 'Workhorse';
	return 'Scorer';
}
