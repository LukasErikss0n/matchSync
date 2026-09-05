import threading
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from routers import admin, calendar, leagues, matches, support
from scripts.backfill_full_history import main as backfill_full_history
from security import require_api_key
from tasks.runner import fetcher_state, run_fetch
from tasks.prune_subscriptions import prune_subscriptions


def _startup_fetch() -> None:
    backfill_full_history(None)
    run_fetch()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    scheduler = BackgroundScheduler(timezone="Europe/Stockholm")
    scheduler.add_job(run_fetch, "cron", hour="17-23", minute="0,30")
    scheduler.add_job(run_fetch, "cron", hour="0,4,8,12,16", minute=0)
    scheduler.add_job(prune_subscriptions, "cron", hour=4, minute=15)
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
app.include_router(calendar.router, prefix="/api")
app.include_router(
    matches.router, prefix="/api", dependencies=[Depends(require_api_key)]
)
app.include_router(
    support.router, prefix="/api", dependencies=[Depends(require_api_key)]
)
app.include_router(
    admin.router, prefix="/api", dependencies=[Depends(require_api_key)]
)


@app.get("/api/last-updated")
def last_updated():
    return {"last_run": fetcher_state["last_run"]}


@app.get("/health")
def health():
    try:
        with Session(engine) as session:
            session.exec(select(1))
        db_ok = True
    except Exception:
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
