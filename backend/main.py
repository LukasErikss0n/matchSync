import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from routers import calendar, leagues, matches
from tasks.fetcher import run_fetch, fetcher_state


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
    threading.Thread(target=run_fetch, daemon=True).start()

    yield

    scheduler.shutdown()


app = FastAPI(title="MatchSync API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leagues.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(matches.router, prefix="/api")


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
