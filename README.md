# Eighty-Two & Oh 🏒

A hockey roster game in the spirit of [82-0.com](https://www.82-0.com/) and
[20-0.com](https://www.20-0.com/). Draft six NHL legends from across history — 3
forwards, 2 defensemen, 1 goalie — and a non-linear engine projects your record
out of 82. Ratings are **era-adjusted and hidden**. Can you go **82-0**?

Live at **eightytwoando.com** (see [DEPLOY.md](DEPLOY.md)).

## How it works

- **Data** — every NHL skater/goalie season since **1929-30** (the forward-pass
  rule change; pre-1930 hockey is a different sport) is pulled from the public
  NHL Stats API. Counting stats only, so the model is fair across all eras.
- **Era-adjusted hidden ratings** — Hockey-Reference-style adjusted stats →
  within-season normal-CDF → a 0-99 rating per category, judged only against a
  player's own-era peers.
- **Five categories** — Scoring · Playmaking · Two-Way · Goaltending · Durability.
  Team strength is a position-weighted geometric mean, so one weak axis caps you.
- See [DESIGN.md](DESIGN.md) for the full methodology and locked decisions.

## Layout

```
pipeline/     stdlib-only Python data pipeline
  pull_seasons.py    NHL API  -> data/raw/
  build_dataset.py   era ratings -> web/src/lib/data/players.json
  tune_curve.py      simulate to set the win-curve constants
  gen_og.py          render the default OG share image
web/          SvelteKit app (Cloudflare Pages)
```

## Develop

```bash
# data (only needed to (re)generate the dataset; players.json is committed)
python3 pipeline/pull_seasons.py
python3 pipeline/build_dataset.py

# app
cd web
npm install
npm run dev        # http://localhost:5173
npm run build
node scripts/smoke.mjs   # headless click-through smoke test (needs chromium)
```

Not affiliated with the NHL. Stats are facts from the public NHL API; no NHL
trademarks or logos are used.
