"""Tune the Layer-2 win curve by simulation.

Team strength = position-weighted MEAN per axis -> geometric mean across the five
axes (so one weak axis caps you, like 20-0 football's mean + convex curve). We
anchor the scale to the best achievable roster so a near-perfect balanced six can
just reach 82-0, experts land in A, and random drafts land in C/D.

  projWins = 82 * min(1, geomean(axes)/ANCHOR) ** P

Prints distributions for random vs expert vs ceiling drafts so we can lock P,
ANCHOR, and the grade bands. Stdlib only.  Run: python3 pipeline/tune_curve.py
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

random.seed(82)
POOL = json.loads((Path(__file__).parent.parent / "web/src/lib/data/players.json").read_text())["pool"]

AXES = ["scoring", "playmaking", "twoway", "goaltending", "durability"]
W = {
    "C": {"scoring": 1.15, "playmaking": 1.20, "twoway": 0.30, "goaltending": 0, "durability": 1.0},
    "L": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0.25, "goaltending": 0, "durability": 1.0},
    "R": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0.25, "goaltending": 0, "durability": 1.0},
    "D": {"scoring": 0.50, "playmaking": 0.70, "twoway": 1.60, "goaltending": 0, "durability": 1.0},
    "G": {"scoring": 0, "playmaking": 0, "twoway": 0, "goaltending": 1.0, "durability": 1.0},
}
SLOTS = ["F", "F", "F", "D", "D", "G"]

by_pos = defaultdict(list)
for p in POOL:
    by_pos[p["grp"]].append(p)
# index by (grp) -> list, and by (team,decade,grp) for rolls
by_td = defaultdict(list)
for p in POOL:
    by_td[(p["team"], p["decade"], p["grp"])].append(p)
roll_keys = defaultdict(list)
for (t, d, g) in by_td:
    roll_keys[g].append((t, d))


def team_axes(roster):
    out = {}
    for k in AXES:
        num = den = 0.0
        for pl in roster:
            w = W[pl["pos"]][k]
            num += w * pl["axes"][k]
            den += w
        out[k] = num / den if den else 0.0
    return out


def geomean(axes):
    prod = 1.0
    for k in AXES:
        prod *= max(axes[k], 1e-6)
    return prod ** (1 / len(AXES))


def strength(roster):
    return geomean(team_axes(roster))


def draft_random():
    """Casual: one roll per slot, a random player from it."""
    roster = []
    for g in SLOTS:
        t, d = random.choice(roll_keys[g])
        roster.append(random.choice(by_td[(t, d, g)]))
    return roster


def draft_expert(rolls_per_slot=3):
    """Expert: for each slot see N rolls (models rerolls/selectivity) and take the
    best available player of the needed position."""
    roster = []
    for g in SLOTS:
        best = None
        for _ in range(rolls_per_slot):
            t, d = random.choice(roll_keys[g])
            cand = max(by_td[(t, d, g)], key=lambda p: p["overall"])
            if best is None or cand["overall"] > best["overall"]:
                best = cand
        roster.append(best)
    return roster


def ceiling():
    """Best achievable roster (global best per slot) — the 82-0 anchor."""
    fs = sorted(by_pos["F"], key=lambda p: -p["overall"])[:3]
    ds = sorted(by_pos["D"], key=lambda p: -p["overall"])[:2]
    g = max(by_pos["G"], key=lambda p: p["axes"]["goaltending"])
    return fs + ds + [g]


def pct(vals, q):
    return sorted(vals)[min(len(vals) - 1, int(q * len(vals)))]


def main():
    ceil_roster = ceiling()
    ceil_s = strength(ceil_roster)
    ceil_axes = team_axes(ceil_roster)
    print("CEILING roster:", [(p["name"], p["pos"]) for p in ceil_roster])
    print("CEILING axes:", {k: round(v, 1) for k, v in ceil_axes.items()}, "geomean=", round(ceil_s, 2))

    N = 20000
    rand_s = [strength(draft_random()) for _ in range(N)]
    exp_s = [strength(draft_expert(3)) for _ in range(N)]
    print(f"\nstrength geomean — random: p50={pct(rand_s,.5):.1f} p90={pct(rand_s,.9):.1f} max={max(rand_s):.1f}")
    print(f"strength geomean — expert: p50={pct(exp_s,.5):.1f} p90={pct(exp_s,.9):.1f} p99={pct(exp_s,.99):.1f} max={max(exp_s):.1f}")

    # ANCHOR slightly below ceiling so a near-optimal six can reach 82-0 but rarely
    for ANCHOR_SCALE in (0.985, 0.99, 1.0):
        ANCHOR = ceil_s * ANCHOR_SCALE
        for P in (2.0, 2.5, 3.0):
            def wins(s):
                return round(82 * min(1.0, s / ANCHOR) ** P)
            rw = [wins(s) for s in rand_s]
            ew = [wins(s) for s in exp_s]
            perfect = sum(1 for w in ew if w >= 82) / N
            print(f"\nANCHOR={ANCHOR:.1f}(x{ANCHOR_SCALE}) P={P}: "
                  f"random[p50={pct(rw,.5)} p90={pct(rw,.9)}] "
                  f"expert[p50={pct(ew,.5)} p90={pct(ew,.9)} p99={pct(ew,.99)} max={max(ew)}] "
                  f"82-0 rate(expert)={perfect*100:.2f}%")


if __name__ == "__main__":
    main()
