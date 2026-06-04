"""Pull full-history NHL season counting stats from the official NHL Stats API.

For every season from 1929-30 (the forward-pass era cutoff) through the current
season we fetch the per-player season summary for skaters and goalies and cache
the raw `data` array to disk. Stdlib only — no third-party deps.

  data/raw/skaters/{seasonId}.json   list[skater-season dict]
  data/raw/goalies/{seasonId}.json   list[goalie-season dict]

Resumable: a season already on disk is skipped, so re-runs only fetch what's
missing. The 2004-05 lockout (seasonId 20042005) legitimately returns 0 rows and
is cached as an empty list.

Run:  python3 pipeline/pull_seasons.py
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

# 1929-30 is the cutoff: forward passing legalized in all zones, scoring tripled
# (1.45 -> 2.95 goals/game). Everything before is a structurally different game.
FIRST_SEASON_START = 1929
LAST_SEASON_START = 2025  # 2025-26; bump as seasons are added

BASE = "https://api.nhle.com/stats/rest/en"
RAW = Path(__file__).parent / "data" / "raw"
UA = "Mozilla/5.0 (eightytwoandoh data pull; contact desalvio23@gmail.com)"
SORT = {
    "skater": '[{"property":"points","direction":"DESC"}]',
    "goalie": '[{"property":"wins","direction":"DESC"}]',
}


def season_ids() -> list[int]:
    return [int(f"{y}{y + 1}") for y in range(FIRST_SEASON_START, LAST_SEASON_START + 1)]


def fetch(kind: str, season_id: int, retries: int = 5) -> list[dict]:
    """Fetch an entire season in one request (limit=-1) for skaters or goalies."""
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "start": "0",
        "limit": "-1",
        "sort": SORT[kind],
        "cayenneExp": f"seasonId={season_id} and gameTypeId=2",
    }
    url = f"{BASE}/{kind}/summary?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode())
            return payload.get("data", [])
        except Exception as e:  # noqa: BLE001 — transient network/HTTP, back off and retry
            wait = 2 ** attempt
            if attempt < retries - 1:
                print(f"    {kind} {season_id} failed ({e}); retry in {wait}s")
                time.sleep(wait)
            else:
                raise
    return []


def pull(kind: str, season_id: int) -> int:
    out = RAW / f"{kind}s" / f"{season_id}.json"
    if out.exists():
        return -1  # already cached
    rows = fetch(kind, season_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows))
    tmp.rename(out)
    time.sleep(0.3)  # be a polite citizen of an undocumented API
    return len(rows)


def main() -> None:
    seasons = season_ids()
    print(f"pulling {len(seasons)} seasons: {seasons[0]} .. {seasons[-1]}")
    total_sk = total_g = 0
    for sid in seasons:
        nk = pull("skater", sid)
        ng = pull("goalie", sid)
        if nk == -1 and ng == -1:
            continue
        total_sk += max(nk, 0)
        total_g += max(ng, 0)
        print(f"  {sid}: skaters={nk if nk >= 0 else 'cached'} goalies={ng if ng >= 0 else 'cached'}")
    print(f"done. new skater rows={total_sk} goalie rows={total_g}")


if __name__ == "__main__":
    main()
