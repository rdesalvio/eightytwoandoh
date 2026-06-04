# Deploying Eighty-Two & Oh

Fully static + edge-function app. Recommended host: **Cloudflare Pages** (free,
unlimited bandwidth, free HTTPS, bundled Workers for future dynamic OG cards).

## 1. Cloudflare Pages

The SvelteKit app lives in `web/` and uses `@sveltejs/adapter-cloudflare`.

**Option A — Git integration (recommended).** Push this repo to GitHub, then in
the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to Git**.

| Setting | Value |
|---|---|
| Framework preset | SvelteKit |
| Root directory | `web` |
| Build command | `npm run build` |
| Build output directory | `.svelte-kit/cloudflare` |
| Node version | 20 or 22 (set `NODE_VERSION=22` env var) |

Every push to `main` redeploys. Free tier = 500 builds/month.

**Option B — Direct upload (no GitHub).**
```bash
cd web
npm run build
npx wrangler pages deploy .svelte-kit/cloudflare --project-name eightytwoandoh
```

## 2. Point eightytwoando.com at it

You bought the domain through Squarespace. Two paths:

**Root domain (eightytwoando.com) — move DNS to Cloudflare.** Cleanest, enables
apex via CNAME flattening. Only do this if the domain isn't running a Squarespace
site or Squarespace/Google email.
1. In Cloudflare, add the site `eightytwoando.com` (free plan). It gives you two
   nameservers.
2. Squarespace → Domains → `eightytwoando.com` → DNS → **Domain Nameservers →
   Use Custom Nameservers**, accept disabling DNSSEC, enter Cloudflare's two
   nameservers, Save. (Up to 48h to propagate.)
3. Cloudflare Pages → your project → **Custom domains** → add `eightytwoando.com`
   and `www`. Cloudflare auto-creates the records and provisions SSL.

**Subdomain only — no nameserver change.** Keep Squarespace DNS and serve from
e.g. `play.eightytwoando.com`: add a **CNAME** in Squarespace DNS pointing to your
`<project>.pages.dev` target. (Cloudflare Pages can't serve the bare apex via
external DNS — use the nameserver path for the root.)

> Do **not** host the game on Squarespace itself — code injection can't run a
> real SPA and blocks CORS.

## 3. Refreshing data each season

```bash
python3 pipeline/pull_seasons.py        # bump LAST_SEASON_START first
python3 pipeline/build_dataset.py        # rewrites web/src/lib/data/players.json
python3 pipeline/tune_curve.py           # sanity-check the curve if the pool grew a lot
```
Commit the regenerated `players.json` and push — Pages redeploys.

## Fast-follows (not blocking launch)
- **Dynamic per-roster OG cards.** Add a Pages Function on `/r/[code]` that decodes
  the roster and renders a 1200×630 PNG (via `workers-og`/satori) for rich
  iMessage/Discord/Twitter previews. Today shared links use the static
  `og-default.png`; the in-app "Share as image" already produces a per-result PNG.
- **Leaderboard / accounts** (optional) via Cloudflare KV or D1.
