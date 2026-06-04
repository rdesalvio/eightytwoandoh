"""Turn raw NHL season stats into the era-adjusted, hidden-rating draft dataset.

Two-layer model (see DESIGN.md):
  Layer 1 — per player-season, era-adjust counting stats (Hockey-Reference style)
            then convert to a within-season normal-CDF rating (0-99) against the
            relevant peer group. This is era-fairness: a 1930s player is rated
            only against 1930s peers.
  Layer 2 — (lives in the web engine) combine the 6 drafted players' axis ratings
            into a team strength and a non-linear win curve.

Output: web/src/lib/data/players.json  — a flat list of draftable "stints"
        (player × franchise × decade = their best season in that window).

Stdlib only.  Run:  python3 pipeline/build_dataset.py
"""
from __future__ import annotations

import json
import math
import statistics
import urllib.request
from collections import defaultdict
from pathlib import Path

RAW = Path(__file__).parent / "data" / "raw"
OUT = Path(__file__).parent.parent / "web" / "src" / "lib" / "data" / "players.json"
NORM = statistics.NormalDist(0, 1)

# Hockey-Reference adjusted-stat targets (combined, both teams).
TARGET_GPG = 6.0
TARGET_APG = 10.0  # 1.67 assists/goal

# Layer-2 win-curve engine (tuned in tune_curve.py). Embedded in the dataset so
# the JS engine and the Python tuner share one source of truth.
AXES_ORDER = ["scoring", "playmaking", "twoway", "goaltending", "durability"]
SLOTS = ["F", "F", "F", "D", "D", "G"]
ENGINE_WEIGHTS = {
    "C": {"scoring": 1.15, "playmaking": 1.20, "twoway": 0.30, "goaltending": 0, "durability": 1.0},
    "L": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0.25, "goaltending": 0, "durability": 1.0},
    "R": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0.25, "goaltending": 0, "durability": 1.0},
    "D": {"scoring": 0.50, "playmaking": 0.70, "twoway": 1.60, "goaltending": 0, "durability": 1.0},
    "G": {"scoring": 0, "playmaking": 0, "twoway": 0, "goaltending": 1.0, "durability": 1.0},
}
CURVE_P = 2.5
ANCHOR_SCALE = 0.99
# Durability is a fun but obscure axis — keep it as a lighter factor in the
# (weighted) geometric mean so it never dominates / over-caps a roster.
AXIS_WEIGHTS = {"scoring": 1.0, "playmaking": 1.0, "twoway": 1.0, "goaltending": 1.0, "durability": 0.5}
# record -> grade ladder (minWins, grade, label, color) — vintage almanac palette
GRADES = [
    [82, "S+", "Immortal", "#a9772a"],
    [76, "A+", "Dynasty", "#9c0c22"],
    [70, "A", "Cup Favorite", "#c8102e"],
    [57, "B", "Contender", "#1d2c49"],
    [44, "C", "Playoff Team", "#6b6228"],
    [30, "D", "Lottery Bound", "#8a7d68"],
    [0, "F", "Tank Job", "#9a3b32"],
]


def _team_axes(roster):
    out = {}
    for k in AXES_ORDER:
        num = den = 0.0
        for pl in roster:
            w = ENGINE_WEIGHTS[pl["pos"]][k]
            num += w * pl["axes"][k]
            den += w
        out[k] = num / den if den else 0.0
    return out


def _geomean(axes):
    logsum = wsum = 0.0
    for k in AXES_ORDER:
        w = AXIS_WEIGHTS[k]
        logsum += w * math.log(max(axes[k], 1e-6))
        wsum += w
    return math.exp(logsum / wsum)


def compute_anchor(players):
    """Best achievable roster's strength -> the 82-0 anchor."""
    fs = sorted((p for p in players if p["grp"] == "F"), key=lambda p: -p["overall"])[:3]
    ds = sorted((p for p in players if p["grp"] == "D"), key=lambda p: -p["overall"])[:2]
    g = max((p for p in players if p["grp"] == "G"), key=lambda p: p["axes"]["goaltending"])
    return _geomean(_team_axes(fs + ds + [g]))


def max_skaters(start_year: int) -> int:
    if start_year >= 1982:
        return 18
    if start_year >= 1971:
        return 17
    if start_year >= 1960:
        return 16
    if start_year >= 1950:
        return 15
    return 14


def decade_label(start_year: int) -> str:
    base = (start_year // 10) * 10
    if start_year == 1929:  # cutoff season belongs to the modern 1930s bucket
        base = 1930
    return f"{base}s"


def phi99(z: float) -> int:
    return max(0, min(99, round(99 * NORM.cdf(z))))


def zscore(x: float, mu: float, sd: float) -> float:
    return (x - mu) / sd if sd > 1e-9 else 0.0


def mean_sd(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0] if values else 0.0), 1.0
    return statistics.fmean(values), (statistics.pstdev(values) or 1.0)


# ----------------------------------------------------------------------------- load


def load_seasons(kind: str) -> dict[int, list[dict]]:
    out = {}
    for f in sorted((RAW / kind).glob("*.json")):
        rows = json.loads(f.read_text())
        if rows:
            out[int(f.stem)] = rows
    return out


def team_name_map() -> dict[str, str]:
    """triCode -> full name from the NHL team endpoint, plus defunct fallbacks."""
    cache = RAW / "teams.json"
    if cache.exists():
        data = json.loads(cache.read_text())
    else:
        url = "https://api.nhle.com/stats/rest/en/team"
        req = urllib.request.Request(url, headers={"User-Agent": "eightytwoandoh"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode()).get("data", [])
        cache.write_text(json.dumps(data))
    names = {t["triCode"]: t["fullName"] for t in data if t.get("triCode")}
    # Defunct / historical teams the modern endpoint may omit.
    names.update({
        "MMR": "Montreal Maroons", "NYA": "New York Americans", "BRK": "Brooklyn Americans",
        "OTT": "Ottawa Senators", "PIR": "Pittsburgh Pirates", "QUA": "Philadelphia Quakers",
        "SEN": "Ottawa Senators", "DCG": "Detroit Cougars", "DFL": "Detroit Falcons",
        "CAT": "Chicago Black Hawks", "TStP": "St. Louis Eagles", "SLE": "St. Louis Eagles",
        "AFM": "Atlanta Flames", "CLR": "Colorado Rockies", "KCS": "Kansas City Scouts",
        "CGS": "California Golden Seals", "OAK": "Oakland Seals", "MNS": "Minnesota North Stars",
        "CLE": "Cleveland Barons", "HAR": "Hartford Whalers", "QUE": "Quebec Nordiques",
        "WIN": "Winnipeg Jets (1979)", "ATL": "Atlanta Thrashers", "PHX": "Phoenix Coyotes",
        "ARI": "Arizona Coyotes", "TAN": "Toronto Arenas", "TSP": "Toronto St. Patricks",
        "NYR": "New York Rangers", "CHI": "Chicago Blackhawks",
    })
    return names


# -------------------------------------------------------------- season context


def season_context(start_year: int, skaters: list[dict], goalies: list[dict]) -> dict:
    sched = max((s.get("gamesPlayed") or 0) for s in skaters) if skaters else 1
    sched = max(sched, 1)
    teams: set[str] = set()
    for row in (*skaters, *goalies):
        for t in (row.get("teamAbbrevs") or "").split(","):
            if t:
                teams.add(t)
    n_teams = max(len(teams), 2)
    team_games = n_teams * sched
    total_goals = sum((s.get("goals") or 0) for s in skaters)
    total_assists = sum((s.get("assists") or 0) for s in skaters)
    # combined (both-teams) per-game rates
    combined_gpg = 2 * total_goals / team_games
    combined_apg = 2 * total_assists / team_games
    lg_gaa = total_goals / team_games  # goals against per team-game
    # league save% (post-1955 only)
    sa = sum((g.get("shotsAgainst") or 0) for g in goalies)
    sv = sum((g.get("saves") or 0) for g in goalies)
    lg_svpct = (sv / sa) if sa > 0 else None
    return {
        "start_year": start_year, "sched": sched, "n_teams": n_teams,
        "team_games": team_games, "total_goals": total_goals,
        "total_assists": total_assists, "combined_gpg": combined_gpg,
        "combined_apg": combined_apg, "lg_gaa": lg_gaa, "lg_svpct": lg_svpct,
        "max_skaters": max_skaters(start_year),
        "assists_conf": 1.0 if start_year >= 1936 else 0.7,  # 3-assist era
    }


# ------------------------------------------------------------- adjusted stats


def adjusted(stat: float, own: float, total: float, target: float, ctx: dict) -> float:
    """HR-style adjusted goal/assist total, excluding the player's own output
    from the league baseline."""
    base_rate = 2 * (total - own) / ctx["team_games"]  # combined per-game, excl player
    era = target / base_rate if base_rate > 1e-9 else 1.0
    sched_adj = 82 / ctx["sched"]
    roster_adj = ctx["max_skaters"] / 18
    return stat * sched_adj * roster_adj * era


# -------------------------------------------------------------------- ratings


POS_GROUP = {"C": "F", "L": "F", "R": "F", "D": "D"}


def build():
    skaters_by_season = load_seasons("skaters")
    goalies_by_season = load_seasons("goalies")
    names = team_name_map()

    # career totals (longevity) within range
    career_gp: dict[int, int] = defaultdict(int)
    for rows in skaters_by_season.values():
        for s in rows:
            career_gp[s["playerId"]] += s.get("gamesPlayed") or 0
    for rows in goalies_by_season.values():
        for g in rows:
            career_gp[g["playerId"]] += g.get("gamesPlayed") or 0

    # one rated record per player-season, keyed by (player, season)
    rated: list[dict] = []

    for sid, skaters in skaters_by_season.items():
        start_year = sid // 10000
        goalies = goalies_by_season.get(sid, [])
        ctx = season_context(start_year, skaters, goalies)
        sched = ctx["sched"]
        gate = max(10, 0.30 * sched)         # draftable / rate-eligible
        reg_gate = max(15, 0.50 * sched)     # "regular" — defines the distribution

        # --- per-skater raw metrics
        recs = []
        for s in skaters:
            pos = s.get("positionCode") or "C"
            grp = POS_GROUP.get(pos, "F")
            gp = s.get("gamesPlayed") or 0
            g, a = s.get("goals") or 0, s.get("assists") or 0
            adj_g = adjusted(g, g, ctx["total_goals"], TARGET_GPG, ctx)
            adj_a = adjusted(a, a, ctx["total_assists"], TARGET_APG, ctx)
            recs.append({
                "row": s, "pos": pos, "grp": grp, "gp": gp,
                "adj_g": adj_g, "adj_a": adj_a, "adj_p": adj_g + adj_a,
                "pm": s.get("plusMinus"), "sh": s.get("shPoints"),
                "pim": s.get("penaltyMinutes") or 0,
            })

        regulars = [r for r in recs if r["gp"] >= reg_gate]
        F = [r for r in regulars if r["grp"] == "F"]
        D = [r for r in regulars if r["grp"] == "D"]

        # distributions
        g_mu, g_sd = mean_sd([r["adj_g"] for r in regulars])
        a_mu, a_sd = mean_sd([r["adj_a"] for r in regulars])
        # two-way: position-specific
        dpts_mu, dpts_sd = mean_sd([r["adj_p"] for r in D]) if D else (0, 1)
        dpm = [r["pm"] for r in D if r["pm"] is not None]
        dpm_mu, dpm_sd = mean_sd(dpm) if dpm else (0, 1)
        fsh = [r["sh"] for r in F if r["sh"] is not None]
        fsh_mu, fsh_sd = mean_sd(fsh) if fsh else (0, 1)
        # durability per group
        def dur_dist(group):
            gp_mu, gp_sd = mean_sd([r["gp"] for r in group])
            cgp_mu, cgp_sd = mean_sd([career_gp[r["row"]["playerId"]] for r in group])
            pim_mu, pim_sd = mean_sd([r["pim"] for r in group])
            return gp_mu, gp_sd, cgp_mu, cgp_sd, pim_mu, pim_sd
        durF = dur_dist(F) if F else (0, 1, 0, 1, 0, 1)
        durD = dur_dist(D) if D else (0, 1, 0, 1, 0, 1)

        for r in recs:
            if r["gp"] < gate:
                continue
            grp, row = r["grp"], r["row"]
            scoring = phi99(zscore(r["adj_g"], g_mu, g_sd))
            playmaking = phi99(zscore(r["adj_a"], a_mu, a_sd))
            # two-way
            if grp == "D":
                z_pts = zscore(r["adj_p"], dpts_mu, dpts_sd)
                if r["pm"] is not None:
                    z_pm = zscore(r["pm"], dpm_mu, dpm_sd)
                    tw = 0.6 * z_pts + 0.4 * z_pm
                else:
                    tw = z_pts
            else:
                # forwards: two-way = penalty-kill / defensive usage (SH points),
                # NOT plus/minus (which just tracks linemate offense). Without SH
                # data (pre-1955) forwards sit neutral, leaving the axis to the D.
                tw = zscore(r["sh"], fsh_mu, fsh_sd) if (r["sh"] is not None and fsh) else 0.0
            twoway = phi99(tw)
            # durability
            gp_mu, gp_sd, cgp_mu, cgp_sd, pim_mu, pim_sd = durF if grp == "F" else durD
            dur = (0.45 * zscore(r["gp"], gp_mu, gp_sd)
                   + 0.35 * zscore(career_gp[row["playerId"]], cgp_mu, cgp_sd)
                   + 0.20 * zscore(r["pim"], pim_mu, pim_sd))
            durability = phi99(dur)

            if grp == "F":
                overall = round(0.42 * scoring + 0.40 * playmaking + 0.10 * twoway + 0.08 * durability)
            else:
                overall = round(0.20 * scoring + 0.28 * playmaking + 0.42 * twoway + 0.10 * durability)

            rated.append({
                "id": row["playerId"], "name": row["skaterFullName"], "pos": r["pos"],
                "grp": grp, "season": sid, "teams": row.get("teamAbbrevs", ""),
                "axes": {"scoring": scoring, "playmaking": playmaking, "twoway": twoway,
                          "goaltending": 0, "durability": durability},
                "overall": overall,
                "conf": ctx["assists_conf"],
                "stats": {"gp": r["gp"], "g": row.get("goals") or 0, "a": row.get("assists") or 0,
                           "p": row.get("points") or 0, "pim": r["pim"], "pm": r["pm"]},
            })

        # --- goalies
        g_gate = max(8, 0.25 * sched)
        greg = [g for g in goalies if (g.get("gamesPlayed") or 0) >= g_gate]
        lg_sv = ctx["lg_svpct"]
        gsaa, svaa, gaa_idx = {}, {}, {}
        for g in greg:
            pid = g["playerId"]
            ga = g.get("goalsAgainst") or 0
            sa = g.get("shotsAgainst")
            if lg_sv is not None and sa:
                gsaa[pid] = lg_sv * sa - ga
                svaa[pid] = (g.get("savePct") or 0) - lg_sv
            ga_avg = g.get("goalsAgainstAverage")
            if ga_avg and ga_avg > 0:
                gaa_idx[pid] = ctx["lg_gaa"] / ga_avg
        post55 = bool(gsaa)
        if post55:
            gsaa_mu, gsaa_sd = mean_sd(list(gsaa.values()))
            svaa_mu, svaa_sd = mean_sd(list(svaa.values()))
        else:
            idx_mu, idx_sd = mean_sd(list(gaa_idx.values())) if gaa_idx else (1, 1)
        gdur_gp_mu, gdur_gp_sd = mean_sd([(g.get("gamesPlayed") or 0) for g in greg]) if greg else (0, 1)
        gdur_c_mu, gdur_c_sd = mean_sd([career_gp[g["playerId"]] for g in greg]) if greg else (0, 1)

        for g in goalies:
            gp = g.get("gamesPlayed") or 0
            if gp < g_gate:
                continue
            pid = g["playerId"]
            if post55 and pid in gsaa:
                goaltending = phi99(0.7 * zscore(gsaa[pid], gsaa_mu, gsaa_sd)
                                    + 0.3 * zscore(svaa[pid], svaa_mu, svaa_sd))
                conf = 1.0
            elif pid in gaa_idx:
                goaltending = phi99(zscore(gaa_idx[pid], idx_mu, idx_sd))
                conf = 0.65
            else:
                continue
            durability = phi99(0.6 * zscore(gp, gdur_gp_mu, gdur_gp_sd)
                               + 0.4 * zscore(career_gp[pid], gdur_c_mu, gdur_c_sd))
            overall = round(0.85 * goaltending + 0.15 * durability)
            rated.append({
                "id": pid, "name": g["goalieFullName"], "pos": "G", "grp": "G",
                "season": sid, "teams": g.get("teamAbbrevs", ""),
                "axes": {"scoring": 0, "playmaking": 0, "twoway": 0,
                          "goaltending": goaltending, "durability": durability},
                "overall": overall, "conf": conf,
                "stats": {"gp": gp, "w": g.get("wins") or 0, "l": g.get("losses") or 0,
                           "gaa": round(g.get("goalsAgainstAverage") or 0, 2),
                           "svp": round(g.get("savePct"), 3) if g.get("savePct") else None,
                           "so": g.get("shutouts") or 0},
            })

    return assemble_stints(rated, names)


# ----------------------------------------------------------- stints + export


def assemble_stints(rated: list[dict], names: dict[str, str]) -> dict:
    """Collapse player-seasons into (player, team, decade) stints, keeping the
    best season as the representative card. Multi-team seasons count for each
    team listed."""
    best: dict[tuple, dict] = {}
    for r in rated:
        start_year = r["season"] // 10000
        dec = decade_label(start_year)
        for tri in r["teams"].split(","):
            if not tri:
                continue
            key = (r["id"], tri, dec)
            if key not in best or r["overall"] > best[key]["overall"]:
                best[key] = r | {"team": tri, "decade": dec}

    # cap per (team, decade, group) to keep the pool sharp
    CAPS = {"F": 10, "D": 6, "G": 4}
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for st in best.values():
        buckets[(st["team"], st["decade"], st["grp"])].append(st)

    players = []
    for (tri, dec, grp), group in buckets.items():
        group.sort(key=lambda s: s["overall"], reverse=True)
        for st in group[: CAPS[grp]]:
            yr = st["season"]
            label = f"{yr // 10000}-{str(yr % 10000)[2:]} {names.get(tri, tri)}"
            players.append({
                "id": st["id"], "name": st["name"], "pos": st["pos"], "grp": grp,
                "team": tri, "decade": dec, "season": yr, "label": label,
                "axes": st["axes"], "overall": st["overall"], "conf": round(st["conf"], 2),
                "stats": st["stats"],
            })

    # teams that actually have players, by decade
    team_decades: dict[str, set] = defaultdict(set)
    used_teams = set()
    for p in players:
        team_decades[p["decade"]].add(p["team"])
        used_teams.add(p["team"])

    decades = sorted({p["decade"] for p in players},
                     key=lambda d: int(d[:-1]) if d[:-1].isdigit() else 0)
    anchor = compute_anchor(players)
    dataset = {
        "meta": {
            "firstSeason": 19291930, "lastSeason": max(p["season"] for p in players),
            "cutoff": "1929-30 (forward passing legalized in all zones; scoring tripled)",
            "players": len(players),
        },
        "engine": {
            "axes": AXES_ORDER, "slots": SLOTS, "weights": ENGINE_WEIGHTS,
            "axisWeights": AXIS_WEIGHTS,
            "anchor": round(anchor * ANCHOR_SCALE, 3), "p": CURVE_P, "grades": GRADES,
        },
        "teams": {t: names.get(t, t) for t in sorted(used_teams)},
        "decades": decades,
        "teamDecades": {d: sorted(ts) for d, ts in team_decades.items()},
        "pool": players,
    }
    return dataset


def main():
    ds = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ds, separators=(",", ":")))
    size_mb = OUT.stat().st_size / 1e6
    print(f"wrote {len(ds['pool'])} stints, {len(ds['teams'])} teams, "
          f"{len(ds['decades'])} decades -> {OUT}  ({size_mb:.2f} MB)")
    # quick face-validity peek
    top = sorted(ds["pool"], key=lambda p: p["overall"], reverse=True)[:12]
    print("\ntop 12 by hidden overall:")
    for p in top:
        print(f"  {p['overall']:>2}  {p['name']:<22} {p['pos']} {p['label']}  axes={p['axes']}")


if __name__ == "__main__":
    main()
