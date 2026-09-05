from datetime import datetime, timezone

from sqlmodel import Session, col, select

from database import engine
from models.models import League, Match, Team
from tasks.fetchers.football import FootballFilter
from tasks.fetchers.swedish_football import SwedishFootballFilter
from tasks.time_management import TimeManagement
from utils import ensure_utc

_POINTS_FOR_WIN = 3
_POINTS_FOR_DRAW = 1

SUPPORTED_LOCAL_LEAGUE_SLUGS = {
    "allsvenskan": SwedishFootballFilter.SEASON_START_MONTH,
    "premier-league": FootballFilter.SEASON_START_MONTH,
}


def _season_start(start_month: int, year: int) -> datetime:
    return datetime(year, start_month, 1, tzinfo=timezone.utc)


def _active_season_year(start_month: int) -> int:
    return int(TimeManagement().get_active_season_year(f"{start_month:02d}"))


def _played(matches: list[Match]) -> list[Match]:
    return [m for m in matches if m.home_score is not None and m.away_score is not None]


def _compute_table(matches: list[Match], teams: list[Team]) -> list[dict]:
    matches = sorted(matches, key=lambda m: m.start_time)
    stats: dict[str, dict] = {
        t.name: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "form": []}
        for t in teams
    }

    for m in matches:
        home, away = m.home_team, m.away_team
        if home not in stats or away not in stats:
            continue
        hs, as_ = m.home_score, m.away_score
        if hs is None or as_ is None:
            continue

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
            "_goals_for": s["gf"],
            "form": s["form"][-5:],
        })

    rows.sort(key=lambda r: (-r["points"], -r["goal_difference"], -r["_goals_for"]))
    for i, row in enumerate(rows, start=1):
        row["position"] = i
        del row["_goals_for"]

    return rows


def _empty_table_ordered_by_last_season(teams: list[Team], previous_season_rows: list[dict]) -> list[dict]:
    last_position = {row["team"]: row["position"] for row in previous_season_rows}
    ordered = sorted(teams, key=lambda t: (last_position.get(t.name, 10_000), t.name))
    return [
        {
            "position": i,
            "team": t.name,
            "played": 0, "won": 0, "drawn": 0, "lost": 0,
            "goal_difference": 0, "points": 0, "form": [],
        }
        for i, t in enumerate(ordered, start=1)
    ]


def get_local_standings(league_slug: str) -> list[dict] | None:
    start_month = SUPPORTED_LOCAL_LEAGUE_SLUGS.get(league_slug)
    if start_month is None:
        return None

    with Session(engine) as session:
        league = session.exec(select(League).where(League.slug == league_slug)).first()
        if league is None:
            return []

        teams = list(session.exec(select(Team).where(Team.league_id == league.id)).all())
        if not teams:
            return []
        team_ids = {t.id for t in teams if t.id is not None}

        all_matches = session.exec(
            select(Match).where(
                col(Match.team_id).in_(team_ids),
                Match.external_id.endswith("_home"),
            )
        ).all()

        active_year = _active_season_year(start_month)
        cutoff_active = _season_start(start_month, active_year)
        cutoff_next = _season_start(start_month, active_year + 1)

        active_season_matches = [
            m for m in all_matches if cutoff_active <= ensure_utc(m.start_time) < cutoff_next
        ]
        next_season_matches = [m for m in all_matches if ensure_utc(m.start_time) >= cutoff_next]

        if next_season_matches:
            played_next = _played(next_season_matches)
            if played_next:
                return _compute_table(played_next, teams)
            previous_rows = _compute_table(_played(active_season_matches), teams)
            return _empty_table_ordered_by_last_season(teams, previous_rows)

        return _compute_table(_played(active_season_matches), teams)
