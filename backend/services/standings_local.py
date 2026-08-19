"""Standings computed from our own Match table rather than any external API —
avoids depending on a third party (rate limits, auth, uptime, format changes)
for data we're already ingesting anyway.

This only works for leagues where scripts/backfill_full_history.py has been
run at least once — the regular periodic fetcher only ever keeps a trailing
10-day window of results (tasks/fetcher.py's RESULTS_WINDOW_DAYS), so without
that one-time backfill this would compute a table missing most of the season.
"""

from datetime import datetime, timezone

from sqlmodel import Session, col, select

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
    "allsvenskan": SwedishFootballFilter.SEASON_START_MONTH,
    "premier-league": FootballFilter.SEASON_START_MONTH,
}


def _season_start(start_month: int, year: int) -> datetime:
    return datetime(year, start_month, 1, tzinfo=timezone.utc)


def _active_season_year(start_month: int) -> int:
    # Reuses TimeManagement's own year-selection logic (tasks/fetcher.py)
    # rather than reimplementing "which year does this season belong to".
    return int(TimeManagement().get_active_season_year(f"{start_month:02d}"))


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _played(matches: list[Match]) -> list[Match]:
    return [m for m in matches if m.home_score is not None and m.away_score is not None]


def _compute_table(matches: list[Match], teams: list[Team]) -> list[dict]:
    """Folds a set of already-played matches into a sorted table. Teams with
    zero matches in the set are dropped — callers that want every team listed
    (e.g. the all-zero pre-season table) handle that themselves."""
    matches = sorted(matches, key=lambda m: m.start_time)
    stats: dict[str, dict] = {
        t.name: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "form": []}
        for t in teams
    }

    for m in matches:
        home, away = m.home_team, m.away_team
        if home not in stats or away not in stats:
            continue  # team since renamed/removed upstream — skip rather than guess
        hs, as_ = m.home_score, m.away_score
        if hs is None or as_ is None:
            continue  # not played — callers pass _played() but don't have to

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


def _empty_table_ordered_by_last_season(teams: list[Team], previous_season_rows: list[dict]) -> list[dict]:
    """Every current team at 0 played, ordered by where they finished last
    season (promoted/newly-tracked teams — no entry last season — sorted
    alphabetically after everyone with a known finish)."""
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

        # Every fixture for this league, played or not (home-perspective row
        # only — each fixture is stored twice, once per team, see DBStore.save).
        # Unplayed ones matter here too: their mere existence is how we detect
        # that next season's schedule has been published.
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
            m for m in all_matches if cutoff_active <= _aware(m.start_time) < cutoff_next
        ]
        next_season_matches = [m for m in all_matches if _aware(m.start_time) >= cutoff_next]

        if next_season_matches:
            # Next season's fixtures already exist in our data — show that
            # season instead of the now-stale completed one: real stats once
            # its games start, or an all-zero table ordered by how last
            # season finished until then.
            played_next = _played(next_season_matches)
            if played_next:
                return _compute_table(played_next, teams)
            previous_rows = _compute_table(_played(active_season_matches), teams)
            return _empty_table_ordered_by_last_season(teams, previous_rows)

        # Next season not published yet — show the current-or-just-finished
        # season's real results (covers both "mid-season" and "season just
        # ended, no new one announced yet").
        return _compute_table(_played(active_season_matches), teams)
