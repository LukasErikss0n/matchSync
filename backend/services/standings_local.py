"""Standings computed from our own Match table rather than any external API —
avoids depending on a third party (rate limits, auth, uptime, format changes)
for data we're already ingesting anyway.

This only works for leagues where scripts/backfill_full_history.py has been
run at least once — the regular periodic fetcher only ever keeps a trailing
10-day window of results (tasks/fetcher.py's RESULTS_WINDOW_DAYS), so without
that one-time backfill this would compute a table missing most of the season.
"""

from datetime import datetime, timezone

from sqlmodel import Session, select

from database import engine
from models.models import League, Match, Team
from tasks.fetcher import FootballFilter, SwedishFootballFilter, TimeManagement

_POINTS_FOR_WIN = 3
_POINTS_FOR_DRAW = 1

# Leagues we've backfilled full match history for and where a single round-robin
# table is a meaningful thing to show (excludes cups/group-stage competitions).
# Value is the season's start month, read directly off the same filter classes
# tasks/fetcher.py uses (SEASON_START_MONTH) rather than copied here, so the
# two can't quietly drift out of sync if one changes.
SUPPORTED_LOCAL_LEAGUE_SLUGS = {
    "allsvenskan": SwedishFootballFilter.SEASON_START_MONTH,   # Mar-Nov
    "premier-league": FootballFilter.SEASON_START_MONTH,       # Aug-May, crosses a calendar-year boundary
}


def _season_cutoff(start_month: int) -> datetime:
    # Reuses TimeManagement's own year-selection logic (tasks/fetcher.py)
    # rather than reimplementing "which year does this season belong to".
    year = int(TimeManagement().get_active_season_year(f"{start_month:02d}"))
    return datetime(year, start_month, 1, tzinfo=timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def get_local_standings(league_slug: str) -> list[dict] | None:
    start_month = SUPPORTED_LOCAL_LEAGUE_SLUGS.get(league_slug)
    if start_month is None:
        return None

    with Session(engine) as session:
        league = session.exec(select(League).where(League.slug == league_slug)).first()
        if league is None:
            return []

        teams = session.exec(select(Team).where(Team.league_id == league.id)).all()
        team_ids = {t.id for t in teams}
        if not team_ids:
            return []

        # Each fixture is stored twice (once per team, see DBStore.save) — read
        # only the home-perspective row so every match is counted once.
        matches = session.exec(
            select(Match).where(
                Match.team_id.in_(team_ids),
                Match.external_id.endswith("_home"),
                Match.home_score.is_not(None),
                Match.away_score.is_not(None),
            )
        ).all()

        cutoff = _season_cutoff(start_month)
        matches = [m for m in matches if _aware(m.start_time) >= cutoff]
        matches.sort(key=lambda m: m.start_time)

        stats: dict[str, dict] = {
            t.name: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "form": []}
            for t in teams
        }

        for m in matches:
            home, away = m.home_team, m.away_team
            if home not in stats or away not in stats:
                continue  # team since renamed/removed upstream — skip rather than guess
            hs, as_ = m.home_score, m.away_score

            stats[home]["played"] += 1
            stats[away]["played"] += 1
            stats[home]["gf"] += hs
            stats[home]["ga"] += as_
            stats[away]["gf"] += as_
            stats[away]["ga"] += hs

            if hs > as_:
                stats[home]["won"] += 1
                stats[away]["lost"] += 1
                stats[home]["form"].append("W")
                stats[away]["form"].append("L")
            elif hs < as_:
                stats[away]["won"] += 1
                stats[home]["lost"] += 1
                stats[home]["form"].append("L")
                stats[away]["form"].append("W")
            else:
                stats[home]["drawn"] += 1
                stats[away]["drawn"] += 1
                stats[home]["form"].append("D")
                stats[away]["form"].append("D")

        rows: list[dict] = []
        for name, s in stats.items():
            if s["played"] == 0:
                continue
            rows.append({
                "team": name,
                "played": s["played"],
                "won": s["won"],
                "drawn": s["drawn"],
                "lost": s["lost"],
                "goal_difference": s["gf"] - s["ga"],
                "points": s["won"] * _POINTS_FOR_WIN + s["drawn"] * _POINTS_FOR_DRAW,
                "_goals_for": s["gf"],   # tie-break only, stripped below
                "form": s["form"][-5:],
            })

        rows.sort(key=lambda r: (-r["points"], -r["goal_difference"], -r["_goals_for"]))
        for i, row in enumerate(rows, start=1):
            row["position"] = i
            del row["_goals_for"]

        return rows
