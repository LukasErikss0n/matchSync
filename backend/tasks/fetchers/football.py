from schemas.schemas import STATUS_FINISHED, STATUS_LIVE, STATUS_SCHEDULED
from tasks.db_store import DBStore
from tasks.http_client import FetchAPI, resolve_pl_badge_year
from tasks.time_management import TimeManagement

_PL_LIVE_PERIODS = frozenset({
    "FirstHalf",
    "HalfTime",
    "SecondHalf",
    "ExtraTimeFirstHalf",
    "ExtraTimeHalfTime",
    "ExtraTimeSecondHalf",
    "ShootOut",
    "PenaltyShootout",
})


def _pl_status(period: str | None) -> str | None:
    if not period:
        return None
    if period == "PreMatch":
        return STATUS_SCHEDULED
    if period == "FullTime":
        return STATUS_FINISHED
    if period in _PL_LIVE_PERIODS:
        return STATUS_LIVE
    return None


class FootballFilter:
    LEAGUES = {
        "premier_league": 8,
        "uefa_champions_league": 5,
        "uefa_conference_league": 1125,
        "fa_cup": 1,
        "efl_cup": 2,
        "uefa_europa_league": 6,
    }
    SEASON_START_MONTH = 8

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _badge_url(self, team: dict) -> str | None:
        team_id = team.get("id")
        if not team_id:
            return None
        yr = resolve_pl_badge_year()
        return f"https://resources.premierleague.com/premierleague{yr}/badges-alt/50/{team_id}.png"

    def _fetch_season(self, league_id: int, season: str, full_history: bool = False) -> dict:
        events: dict = {}
        for week in range(1, 50):
            url = (
                f"https://sdp-prem-prod.premier-league-prod.pulselive.com"
                f"/api/v1/competitions/{league_id}/seasons/{season}/matchweeks/{week}/matches"
            )
            week_data = self.api.get(url)
            if not week_data.get("data"):
                break
            for match in week_data["data"]:
                start = self.time.convert_to_utc(
                    match["kickoff"], match["kickoffTimezone"]
                )
                if not full_history and not self.time.is_recent_or_future(start):
                    continue
                event_id = str(match["matchId"])
                events[event_id] = {
                    "eventId":          event_id,
                    "homeTeam":         match["homeTeam"]["name"],
                    "awayTeam":         match["awayTeam"]["name"],
                    "startDateAndTime": start,
                    "venue":            match.get("ground"),
                    "status":           _pl_status(match.get("period")),
                    "homeIcon":         self._badge_url(match["homeTeam"]),
                    "awayIcon":         self._badge_url(match["awayTeam"]),
                    "homeScore":        match["homeTeam"].get("score"),
                    "awayScore":        match["awayTeam"].get("score"),
                }
        return events

    def filter(self, full_history: bool = False, league_keys: set[str] | None = None):
        season = self.time.get_active_season_year(f"{self.SEASON_START_MONTH:02d}")
        for league_key, league_id in self.LEAGUES.items():
            if league_keys is not None and league_key not in league_keys:
                continue
            events = self._fetch_season(league_id, season, full_history=full_history)
            if full_history:
                next_season = str(int(season) + 1)
                next_events = self._fetch_season(league_id, next_season, full_history=full_history)
                events = {**events, **next_events}
            elif not events:
                next_season = str(int(season) + 1)
                events = self._fetch_season(league_id, next_season, full_history=full_history)
            self.store.save("football", league_key, events)
