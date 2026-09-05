"""Run inside the backend container:
    python3 scripts/backfill_full_history.py
    python3 scripts/backfill_full_history.py allsvenskan premier_league

Supported league keys: allsvenskan, premier_league, shl, sdhl, sblherrar,
sbldamer, f1.
"""

import sys

from sqlmodel import Session

from database import engine
from tasks.db_store import DBStore
from tasks.fetchers.f1 import F1Filter
from tasks.fetchers.football import FootballFilter
from tasks.fetchers.hockey_basketball import HelpFunctions, HockeyBasketballFilter
from tasks.fetchers.swedish_football import SwedishFootballFilter
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement

_HOCKEY_BASKETBALL_LEAGUE_KEYS = {"shl", "sdhl", "sblherrar", "sbldamer"}
_FOOTBALL_LEAGUE_KEYS = {"premier_league"}
_F1_LEAGUE_KEYS = {"f1"}


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


def backfill_f1(store: DBStore, api: FetchAPI, tm: TimeManagement, league_keys: set[str]) -> None:
    if "f1" not in league_keys:
        return
    F1Filter(api, tm, store).filter(full_history=True)
    print("Backfilled f1")


def main(league_keys: list[str] | None) -> None:
    all_keys = {
        "allsvenskan",
        *_FOOTBALL_LEAGUE_KEYS,
        *_HOCKEY_BASKETBALL_LEAGUE_KEYS,
        *_F1_LEAGUE_KEYS,
    }
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
        backfill_f1(store, api, tm, keys)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
