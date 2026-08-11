import threading
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from routers import calendar, leagues, matches
from scripts.backfill_full_history import main as backfill_full_history
from security import require_api_key
from tasks.fetcher import run_fetch, fetcher_state


def _startup_fetch() -> None:
    # Idempotent (upserts by external_id), so it's safe to run on every
    # startup — guarantees local standings (services/standings_local.py) have
    # a full season's history even after a fresh DB, instead of relying on
    # someone remembering to run this by hand. The regular fetcher stays a
    # cheap 10-day window on purpose (see that script's docstring for why
    # always-full-history there would mean re-scraping svenskfotboll.se's
    # entire season every 30 minutes).
    #
    # Run sequentially, not as two concurrent threads — both write to
    # overlapping Team/Match rows (e.g. backfilling premier_league and the
    # regular fetch both touch the same teams), and running them at once
    # caused a real Postgres deadlock between the two transactions.
    backfill_full_history(None)
    run_fetch()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    # Scheduler runs in Europe/Stockholm time (UTC+2 CEST / UTC+1 CET).
    scheduler = BackgroundScheduler(timezone="Europe/Stockholm")
    # 17:00–23:30 local time: run every 30 minutes
    scheduler.add_job(run_fetch, "cron", hour="17-23", minute="0,30")
    # Rest of day: run every 4 hours (0, 4, 8, 12, 16)
    scheduler.add_job(run_fetch, "cron", hour="0,4,8,12,16", minute=0)
    scheduler.start()
    threading.Thread(target=_startup_fetch, daemon=True).start()

    yield

    scheduler.shutdown()


app = FastAPI(title="MatchCalender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    leagues.router, prefix="/api", dependencies=[Depends(require_api_key)]
)
# calendar router handles its own auth: the .ics endpoint must stay public
# (calendar clients can't send headers), the rest requires the key.
app.include_router(calendar.router, prefix="/api")
app.include_router(
    matches.router, prefix="/api", dependencies=[Depends(require_api_key)]
)


@app.get("/api/last-updated")
def last_updated():
    """When the fetcher last completed a successful run — public, not sensitive."""
    return {"last_run": fetcher_state["last_run"]}


@app.get("/health")
def health():
    # Check DB
    try:
        with Session(engine) as session:
            session.exec(select(1))
        db_ok = True
    except Exception as e:
        db_ok = False

    ok = db_ok and fetcher_state["status"] != "error"

    payload = {
        "status": "ok" if ok else "error",
        "db": "ok" if db_ok else "unreachable",
        "fetcher": fetcher_state["status"],
        "fetcher_last_run": fetcher_state["last_run"],
        "fetcher_last_error": fetcher_state["last_error"],
    }

    if not ok:
        raise HTTPException(status_code=503, detail=payload)
    return payload
