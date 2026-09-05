from datetime import datetime

from sqlmodel import Session

from database import engine
from tasks.alerts import send_error_email
from tasks.common import ExpectedUpstreamGap, LOCAL_TZ
from tasks.db_store import DBStore
from tasks.fetchers.f1 import F1Filter
from tasks.fetchers.fifa import FifaFilter
from tasks.fetchers.football import FootballFilter
from tasks.fetchers.football_icons import FootballIconsFetcher
from tasks.fetchers.hockey_basketball import HelpFunctions, HockeyBasketballFilter
from tasks.fetchers.iihf import IIHFFilter
from tasks.fetchers.swedish_football import SwedishFootballFilter
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement

fetcher_state: dict = {
    "last_run": None,
    "last_error": None,
    "status": "pending",
}


def run_fetch() -> None:
    print(f"[fetcher] starting at {datetime.now(LOCAL_TZ).isoformat()}")
    api = FetchAPI()
    time = TimeManagement()
    helpers = HelpFunctions()

    errors: list[str] = []

    def run_one(label: str, fn) -> None:
        try:
            fn()
        except ExpectedUpstreamGap as e:
            print(f"[fetcher] {label} skipped: {e}")
        except Exception as e:
            print(f"[fetcher] {label} failed: {e}")
            errors.append(f"{label}: {e}")

    try:
        with Session(engine) as session:
            store = DBStore(session)
            run_one("football", lambda: FootballFilter(api, time, store).filter())
            run_one("hockey/basketball", lambda: HockeyBasketballFilter(api, time, store, helpers).filter())
            run_one("swedish football", lambda: SwedishFootballFilter(api, time, store).filter())
            run_one("iihf", lambda: IIHFFilter(api, time, store).filter())
            run_one("fifa", lambda: FifaFilter(api, time, store).filter())
            run_one("f1", lambda: F1Filter(api, time, store).filter())
            run_one("football icons", lambda: FootballIconsFetcher(api, store).filter())
            run_one("crest crop", lambda: store.backfill_cropped_crests())

        fetcher_state["last_run"] = datetime.now(LOCAL_TZ).isoformat()
        if errors:
            combined = "; ".join(errors)
            was_ok = fetcher_state["status"] != "error"
            fetcher_state["status"] = "error"
            fetcher_state["last_error"] = combined
            print(f"[fetcher] completed with errors: {combined}")
            if was_ok:
                send_error_email(combined)
        else:
            fetcher_state["status"] = "ok"
            fetcher_state["last_error"] = None
            print("[fetcher] done")
    except Exception as e:
        was_ok = fetcher_state["status"] != "error"
        fetcher_state["status"] = "error"
        fetcher_state["last_error"] = str(e)
        print(f"[fetcher] error: {e}")
        if was_ok:
            send_error_email(str(e))
