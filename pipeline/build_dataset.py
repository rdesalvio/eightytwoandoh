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
AXES_ORDER = ["scoring", "playmaking", "twoway", "goaltending"]
SLOTS = ["F", "F", "F", "D", "D", "G"]
# "twoway" is the DEFENSE axis: driven only by the defensemen (forwards aren't
# judged on something the historical data can't measure).
ENGINE_WEIGHTS = {
    "C": {"scoring": 1.15, "playmaking": 1.20, "twoway": 0, "goaltending": 0, "durability": 1.0},
    "L": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0, "goaltending": 0, "durability": 1.0},
    "R": {"scoring": 1.00, "playmaking": 1.00, "twoway": 0, "goaltending": 0, "durability": 1.0},
    "D": {"scoring": 0.50, "playmaking": 0.70, "twoway": 1.00, "goaltending": 0, "durability": 1.0},
    "G": {"scoring": 0, "playmaking": 0, "twoway": 0, "goaltending": 1.0, "durability": 1.0},
}
GAMES = 16  # 16 wins lift the Stanley Cup (4 playoff rounds x 4 wins)
# Tuned (vs the real 1-roll mechanic) so skilled play reaches the Cup Final most
# games and wins the Cup ~5% of the time — winnable & fun, left-skewed toward wins.
CURVE_P = 2.5
ANCHOR_SCALE = 0.915
# Four equal axes: forwards' Scoring + Playmaking, the D's Defense, the goalie's
# Goaltending. Each group judged on its own job; all era-fair and draftable.
AXIS_WEIGHTS = {"scoring": 1.0, "playmaking": 1.0, "twoway": 1.0, "goaltending": 1.0}
# record -> grade ladder out of 16 (minWins, grade, label, color), themed to the
# playoff rounds — every 4 wins is another round on the way to the Cup.
GRADES = [
    [16, "S+", "Cup Champion", "#ffce54"],
    [12, "A", "Cup Final", "#ff5663"],
    [8, "B", "Conference Final", "#4db6ff"],
    [4, "C", "Second Round", "#5fd38a"],
    [1, "D", "First Round", "#9aa9ba"],
    [0, "F", "Missed Playoffs", "#7c8a99"],
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
            z_sc = zscore(r["adj_g"], g_mu, g_sd)
            z_pl = zscore(r["adj_a"], a_mu, a_sd)
            # two-way
            if grp == "D":
                z_pts = zscore(r["adj_p"], dpts_mu, dpts_sd)
                if r["pm"] is not None:
                    z_tw = 0.6 * z_pts + 0.4 * zscore(r["pm"], dpm_mu, dpm_sd)
                else:
                    z_tw = z_pts
            else:
                # forwards: two-way = penalty-kill / defensive usage (SH points),
                # NOT plus/minus (which just tracks linemate offense). Without SH
                # data (pre-1955) forwards sit neutral, leaving the axis to the D.
                z_tw = zscore(r["sh"], fsh_mu, fsh_sd) if (r["sh"] is not None and fsh) else 0.0
            # durability
            gp_mu, gp_sd, cgp_mu, cgp_sd, pim_mu, pim_sd = durF if grp == "F" else durD
            z_du = (0.45 * zscore(r["gp"], gp_mu, gp_sd)
                    + 0.35 * zscore(career_gp[row["playerId"]], cgp_mu, cgp_sd)
                    + 0.20 * zscore(r["pim"], pim_mu, pim_sd))

            rated.append({
                "id": row["playerId"], "name": row["skaterFullName"], "pos": r["pos"],
                "grp": grp, "season": sid, "teams": row.get("teamAbbrevs", ""),
                "gp": r["gp"], "conf": ctx["assists_conf"],
                "z": {"scoring": z_sc, "playmaking": z_pl, "twoway": z_tw, "durability": z_du},
                "stats": {"g": row.get("goals") or 0, "a": row.get("assists") or 0,
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
                # balance volume (GSAA) with rate (save% vs era) so a workhorse on
                # a bad team can't inflate purely on shots faced.
                gz = 0.45 * zscore(gsaa[pid], gsaa_mu, gsaa_sd) + 0.55 * zscore(svaa[pid], svaa_mu, svaa_sd)
                conf = 1.0
            elif pid in gaa_idx:
                gz = zscore(gaa_idx[pid], idx_mu, idx_sd)
                conf = 0.65
            else:
                continue
            gz_du = 0.6 * zscore(gp, gdur_gp_mu, gdur_gp_sd) + 0.4 * zscore(career_gp[pid], gdur_c_mu, gdur_c_sd)
            rated.append({
                "id": pid, "name": g["goalieFullName"], "pos": "G", "grp": "G",
                "season": sid, "teams": g.get("teamAbbrevs", ""),
                "gp": gp, "conf": conf,
                "z": {"goaltending": gz, "durability": gz_du},
                "graw": {"w": g.get("wins") or 0, "l": g.get("losses") or 0,
                          "so": g.get("shutouts") or 0, "ga": g.get("goalsAgainst") or 0,
                          "saves": g.get("saves") or 0, "sa": g.get("shotsAgainst") or 0,
                          "toi": g.get("timeOnIce") or 0, "gaa": g.get("goalsAgainstAverage") or 0},
            })

    return assemble_stints(rated, names)


# ----------------------------------------------------------- stints + export


def _overall(grp: str, axes: dict) -> int:
    if grp == "F":
        return round(0.52 * axes["scoring"] + 0.48 * axes["playmaking"])
    if grp == "D":
        return round(0.22 * axes["scoring"] + 0.31 * axes["playmaking"] + 0.47 * axes["twoway"])
    return round(axes["goaltending"])


def assemble_stints(rated: list[dict], names: dict[str, str]) -> dict:
    """Collapse player-seasons into one card per (player, team, DECADE) — an era.
    The rating is the games-weighted average of the player's per-season z-scores
    across that decade (each season judged vs its own peers), and the stats are
    decade totals. Multi-team seasons count for each team listed."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rated:
        dec = decade_label(r["season"] // 10000)
        for tri in r["teams"].split(","):
            if tri:
                groups[(r["id"], tri, dec)].append(r)

    stints = []
    for (pid, tri, dec), seasons in groups.items():
        grp = seasons[0]["grp"]
        gp_total = sum(s["gp"] for s in seasons)
        axes = {}
        for k in AXES_ORDER:
            num = wsum = 0.0
            for s in seasons:
                if k in s["z"]:
                    num += s["z"][k] * s["gp"]
                    wsum += s["gp"]
            axes[k] = phi99(num / wsum) if wsum else 0
        if grp == "G":
            ga = sum(s["graw"]["ga"] for s in seasons)
            sa = sum(s["graw"]["sa"] for s in seasons)
            toi = sum(s["graw"]["toi"] for s in seasons)
            gaa = (ga / (toi / 3600) if toi
                   else sum(s["graw"]["gaa"] * s["gp"] for s in seasons) / (gp_total or 1))
            stats = {"gp": gp_total, "w": sum(s["graw"]["w"] for s in seasons),
                     "l": sum(s["graw"]["l"] for s in seasons),
                     "so": sum(s["graw"]["so"] for s in seasons),
                     "gaa": round(gaa, 2),
                     "svp": round(sum(s["graw"]["saves"] for s in seasons) / sa, 3) if sa else None}
        else:
            pms = [s["stats"]["pm"] for s in seasons if s["stats"]["pm"] is not None]
            stats = {"gp": gp_total, "g": sum(s["stats"]["g"] for s in seasons),
                     "a": sum(s["stats"]["a"] for s in seasons),
                     "p": sum(s["stats"]["p"] for s in seasons),
                     "pim": sum(s["stats"]["pim"] for s in seasons),
                     "pm": sum(pms) if pms else None}
        stints.append({
            "id": pid, "name": seasons[0]["name"], "pos": seasons[0]["pos"], "grp": grp,
            "team": tri, "decade": dec, "ns": len(seasons),
            "label": f"{dec} · {names.get(tri, tri)}",
            "axes": axes, "overall": _overall(grp, axes),
            "conf": round(min(s["conf"] for s in seasons), 2), "stats": stats,
        })

    # an "era" should be a real tenure, not a one-season cameo with a random team
    stints = [s for s in stints if s["ns"] >= 2]

    # cap per (team, decade, group) to keep the pool sharp
    CAPS = {"F": 10, "D": 6, "G": 4}
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for st in stints:
        buckets[(st["team"], st["decade"], st["grp"])].append(st)

    players = []
    for group in buckets.values():
        group.sort(key=lambda s: s["overall"], reverse=True)
        players.extend(group[: CAPS[group[0]["grp"]]])

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
            "firstSeason": 19291930, "lastSeason": max(r["season"] for r in rated),
            "cutoff": "1929-30 (forward passing legalized in all zones; scoring tripled)",
            "players": len(players),
        },
        "engine": {
            "axes": AXES_ORDER, "slots": SLOTS, "weights": ENGINE_WEIGHTS,
            "axisWeights": AXIS_WEIGHTS, "games": GAMES,
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
