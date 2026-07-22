"""One-off backfill: pulls a whole season's results into the Match table for
leagues whose regular sync only ever sees a trailing RESULTS_WINDOW_DAYS
window (see tasks/fetcher.py). Needed once per league before local standings
computation (services/standings_local.py) has enough history to be accurate;
the regular periodic fetcher keeps it current from then on.

Run inside the backend container:
    python3 scripts/backfill_full_history.py                        # everything below
    python3 scripts/backfill_full_history.py allsvenskan premier_league  # just these

Supported league keys: allsvenskan, premier_league, shl, sdhl, sblherrar, sbldamer.
(UEFA Champions/Europa/Conference League are deliberately not included: their
fixture feed mixes league-phase and two-legged knockout matches with no
reliable way to tell them apart, so a locally-computed table would start
counting knockout ties as extra league games once the knockout rounds begin.)
"""

import sys

from sqlmodel import Session

from database import engine
from tasks.fetcher import (
    DBStore,
    FetchAPI,
    FootballFilter,
    HelpFunctions,
    HockeyBasketballFilter,
    SwedishFootballFilter,
    TimeManagement,
)

_HOCKEY_BASKETBALL_LEAGUE_KEYS = {"shl", "sdhl", "sblherrar", "sbldamer"}
_FOOTBALL_LEAGUE_KEYS = {"premier_league"}


def backfill_swedish_football(store: DBStore, api: FetchAPI, tm: TimeManagement, league_keys: set[str]) -> None:
    filt = SwedishFootballFilter(api, tm, store)
    for league_key, competition_id in filt.LEAGUES.items():
        if league_key not in league_keys:
            continue
        events: dict = {}
        filt._collect(
            events,
            f"/api/upcoming-games/?competitionId={competition_id}&from=0",
            full_history=True,
        )
        filt._collect(
            events,
            f"/api/played-games/?competitionId={competition_id}&from=0",
            full_history=True,
        )
        store.save("football", league_key, events)
        print(f"Backfilled {league_key}: {len(events)} events")


def backfill_pulselive_football(store: DBStore, api: FetchAPI, tm: TimeManagement, league_keys: set[str]) -> None:
    keys = league_keys & _FOOTBALL_LEAGUE_KEYS
    if not keys:
        return
    filt = FootballFilter(api, tm, store)
    filt.filter(full_history=True, league_keys=keys)
    print(f"Backfilled {sorted(keys)}")


def backfill_hockey_basketball(store: DBStore, api: FetchAPI, tm: TimeManagement, league_keys: set[str]) -> None:
    keys = league_keys & _HOCKEY_BASKETBALL_LEAGUE_KEYS
    if not keys:
        return
    filt = HockeyBasketballFilter(api, tm, store, HelpFunctions())
    filt.filter(full_history=True, league_keys=keys)
    print(f"Backfilled {sorted(keys)}")


def main(league_keys: list[str] | None) -> None:
    all_keys = {"allsvenskan", *_FOOTBALL_LEAGUE_KEYS, *_HOCKEY_BASKETBALL_LEAGUE_KEYS}
    keys = set(league_keys) if league_keys else all_keys
    unknown = keys - all_keys
    if unknown:
        print(f"Unknown league key(s): {sorted(unknown)} — supported: {sorted(all_keys)}")
        return

    with Session(engine) as session:
        api = FetchAPI()
        tm = TimeManagement()
        store = DBStore(session)
        backfill_swedish_football(store, api, tm, keys)
        backfill_pulselive_football(store, api, tm, keys)
        backfill_hockey_basketball(store, api, tm, keys)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
