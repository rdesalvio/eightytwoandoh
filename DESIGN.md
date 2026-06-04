# Eighty-Two and Oh — design

A hockey take on [82-0.com](https://www.82-0.com/) (basketball) and
[20-0.com](https://www.20-0.com/) (football): draft an all-time roster from a
slot machine, and a non-linear engine projects your record out of 82. Perfect =
**82-0**. Domain: **eightytwoando.com**.

## Locked decisions

| Decision | Choice |
|---|---|
| Era cutoff | **1929-30 onward.** Forward passing was legalized in all zones that season and scoring tripled (1.45 → 2.95 G/game) — the cleanest "different game" line in NHL history. Pre-1930 carry-the-puck hockey is excluded. State this in How-to-Play. |
| Roster | **6 players: 3 F, 2 D, 1 G.** |
| Categories | **Balanced 5:** Scoring · Playmaking · Two-Way/Defense · Goaltending · Durability & Grit. |
| v1 modes | Daily Challenge (seeded), Classic ↔ Hockey-IQ toggle, Themed drafts. (Hard mode + Head-to-head deferred.) |
| Stack | SvelteKit, deployed on Cloudflare Pages (free, unlimited bandwidth). |
| Data | Official NHL Stats API (`api.nhle.com/stats/rest`), counting stats only. No HR/MoneyPuck (ToS / modern-only). No NHL logos/trademarks. |

## Why these five categories

Each axis must be computable across **all** included seasons and must be anchored
to a position group so balance is forced. Hits/blocks/TOI only exist since
2005-06 and +/- since 1959-60, so they cannot anchor an all-eras axis — PIM
carries "grit" and D point-share + longevity carry "two-way" instead.

| Axis | Built from | Position emphasis |
|---|---|---|
| Scoring | era-adjusted Goals | Forwards (D light, G none) |
| Playmaking | era-adjusted Assists | Forwards + puck-moving D |
| Two-Way / Defense | D points among D + PIM/+/- where available + longevity at D | **D-led (1.6×)** |
| Goaltending | GSAA & SV%-vs-league (1955+), GAA-vs-league (pre-1955), W%, SO | **Goalie only** |
| Durability & Grit | season GP (availability) + career GP (longevity) + era-capped PIM | Everyone |

## Two-layer rating model

**Layer 1 — player era-fairness (hidden 0-99 per axis).** For each player-season
(1929-30+), compute era-adjusted metrics, then convert to a **within-season
normal-CDF** rating against the relevant peer group. This makes a 1930s player
rated only against 1930s peers — automatically era-fair, bounded [0,99], and
survivorship/expansion robust. The number is never shown; only record + grade +
a post-draft reveal.

Era adjustment = Hockey-Reference Adjusted Stats, counting-stats only:

```
AdjG = G · (82/sched) · (maxSkaters/18) · (6.0  / combinedGPG_excl_player)
AdjA = A · (82/sched) · (maxSkaters/18) · (10.0 / combinedAPG_excl_player)
```

- `sched` = scheduled games (proxied by max skater GP that season → auto-handles
  44/48/70/80/82-game eras and lockout/COVID short seasons).
- `combinedGPG` = both-teams goals/game = `2·totalGoals / (numTeams·sched)`;
  target 6.0. `combinedAPG` target 10.0 (1.67 assists/goal). **Exclude the
  player's own G/A from the baseline** so a dominant scorer doesn't inflate his
  own denominator.
- `maxSkaters` stepwise: ≥1982→18, 1971-81→17, 1960-70→16, 1950-59→15, ≤1949→14.

Peer groups for the CDF:
- scoring / playmaking → all qualifying skaters that season (forwards top it; D
  naturally low, which is correct — they feed those axes only lightly).
- two-way → **position-specific** (D vs D, F vs F) so a shutdown D rates well
  among D.
- durability → position-specific.
- goaltending → all qualifying goalies that season.

Goalie metric: post-1955 = blend of GSAA/game (`lgSV%·SA − GA`) and
SV%-above-league, plus W% and SO rate; pre-1955 = GAA-vs-league index
(`lgGAA/GAA`), flagged lower-confidence. Assists pre-1936 (3-per-goal era) and
pre-1955 goalies carry a `confidence < 1` flag.

**Layer 2 — team strength & the win curve (the 82-0 magic).** Like 20-0
football, team strength is a **position-weighted mean**, not a sum, and the win
curve is **convex at the top** — together these make one weak link cap you. We
add an explicit weakest-axis floor to nail "a deficiency in even one category can
prevent a perfect season."

```
teamAxis[k] = Σ_players w[pos][k]·rating[player][k] / Σ_players w[pos][k]
strength    = geomean(teamAxis[1..5]) / 100
projWins    = 82 · strength^p                       # p ≈ 1.8 (convex)
projWins    = min(projWins, 82 · capCurve(min(teamAxis)/100))   # weakest-axis floor
record      = round(projWins) - (82 - round(projWins))
```

Position weights `w[pos][axis]` (the QB-1.5× analog — goalie owns 100% of
Goaltending = 20% of the geomean from one player):

| | Scoring | Playmaking | Two-Way | Goaltending | Durability |
|---|---|---|---|---|---|
| C | 1.15 | 1.20 | 0.70 | 0 | 1.0 |
| W | 1.00 | 1.00 | 0.50 | 0 | 1.0 |
| D | 0.50 | 0.70 | **1.60** | 0 | 1.0 |
| G | 0 | 0 | 0 | **1.0** | 1.0 |

`p` and `capCurve` are tuned by simulation so a genuinely elite, *balanced* six
can reach 82-0 but rarely (<1-2% of strong drafts). See `pipeline/tune_curve.py`.

## Draft model

The slot machine rolls a **(franchise, decade)** each round; you pick the best
available player of the round's required position. Stints are keyed
`(player, franchise triCode, decade)` with the player's **best qualifying season**
in that window as the representative card. Decades: 1930s (from 1929-30) …
2020s. One free **franchise skip** + one free **era skip** per game (scarce).
Multi-team seasons attribute to each listed team (minor; fine for a game).

Grade ladder (record → grade), mirroring the originals:
S+ 82-0 "Immortal" · A 70-81 · B 57-69 · C 45-56 · D 33-44 · F ≤32 (tune to
distribution).

## Repo layout

```
pipeline/         stdlib-only Python data pipeline
  pull_seasons.py   NHL API → data/raw/{skaters,goalies}/{seasonId}.json
  build_dataset.py  era ratings → web/src/lib/data/players.json
  tune_curve.py     simulate to set the win-curve constants
  data/raw/         cached raw API JSON (gitignored)
web/              SvelteKit app (Cloudflare Pages)
```

## Data sourcing notes

NHL Stats API, no key, complete back to 1917-18 (we start 1929-30). `limit=-1`
returns a whole season per request → ~194 requests, ~40k skater-seasons + ~4k
goalie-seasons for our range. Returns factual stats (not copyrightable); we
redistribute our own derived numbers and use no NHL branding. SV%/shots-against
null before 1955-56; +/- null before 1959-60; PP/SH null in early eras — the
model degrades gracefully.
