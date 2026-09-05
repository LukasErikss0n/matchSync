from dataclasses import dataclass
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from services.cache import MISSING, TTLCache
from tasks.common import LEAGUE_DISPLAY, is_playoff_game_type, slugify
from tasks.fetchers.fifa import FifaFilter
from tasks.fetchers.football import FootballFilter
from tasks.fetchers.hockey_basketball import HelpFunctions, HockeyBasketballFilter
from tasks.fetchers.iihf import IIHFFilter
from tasks.fetchers.swedish_football import SwedishFootballFilter
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement

_cache: TTLCache["SeasonStats"] = TTLCache(ttl_seconds=6 * 60 * 60)

_PROGRESSIVE_KNOCKOUT_SLUGS = {"fa-cup", "efl-cup"}


@dataclass
class SeasonStats:
    season_start: datetime | None
    regular_season_count: int
    published: bool
    progressive_knockout: bool = False


def _slug_to_league_key() -> dict[str, str]:
    return {slugify(name): key for key, name in LEAGUE_DISPLAY.items()}


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _football_starts_for_season(
    api: FetchAPI, time: TimeManagement, league_id: int, season: str
) -> list[datetime]:
    starts: list[datetime] = []
    for week in range(1, 50):
        url = (
            f"https://sdp-prem-prod.premier-league-prod.pulselive.com"
            f"/api/v1/competitions/{league_id}/seasons/{season}/matchweeks/{week}/matches"
        )
        week_data = api.get(url)
        if not week_data.get("data"):
            break
        for match in week_data["data"]:
            dt = _parse_iso(time.convert_to_utc(match["kickoff"], match["kickoffTimezone"]))
            if dt:
                starts.append(dt)
    return starts


def _football_starts(api: FetchAPI, time: TimeManagement, league_id: int) -> list[datetime]:
    season = time.get_active_season_year("08")
    starts = _football_starts_for_season(api, time, league_id, season)
    season_concluded = bool(starts) and max(starts) < datetime.now(timezone.utc)

    if not starts or season_concluded:
        next_season = str(int(season) + 1)
        next_starts = _football_starts_for_season(api, time, league_id, next_season)
        if next_starts:
            return next_starts
        if season_concluded:
            return []
    return starts


def _hockey_basketball_starts(
    api: FetchAPI, helpers: HelpFunctions, url_slug: str
) -> tuple[list[datetime], list[datetime]]:
    meta = api.get(f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter")
    season_uuid, series_uuid, game_types = helpers.get_active_season_uuid(meta)

    all_starts: list[datetime] = []
    regular_starts: list[datetime] = []
    for item in game_types:
        is_playoff = is_playoff_game_type(item)
        url = (
            f"https://www.{url_slug}.se/api/sports-v2/game-schedule"
            f"?seasonUuid={season_uuid}&seriesUuid={series_uuid}"
            f"&gameTypeUuid={item['uuid']}&gamePlace=all&played=all"
        )
        match_data = api.get(url)
        for match in match_data.get("gameInfo", []):
            dt = _parse_iso(match.get("rawStartDateTime", ""))
            if not dt:
                continue
            all_starts.append(dt)
            if not is_playoff:
                regular_starts.append(dt)
    return all_starts, regular_starts


def _svenskfotboll_paginate(
    api: FetchAPI, time: TimeManagement, endpoint: str, competition_id: int
) -> list[datetime]:
    base = "https://www.svenskfotboll.se"
    starts: list[datetime] = []
    next_url = f"/api/{endpoint}/?competitionId={competition_id}&from=0"
    while next_url:
        page = api.get(base + next_url)
        soup = BeautifulSoup(page["data"], "html.parser")
        for match in soup.select(".match-list__match"):
            time_el = match.select_one("time")
            dt_attr = time_el.get("datetime") if time_el else None
            if not isinstance(dt_attr, str) or not dt_attr:
                continue
            dt = _parse_iso(time.convert_to_utc(dt_attr))
            if dt:
                starts.append(dt)
        next_url = page.get("nextUrl")
    return starts


def _swedish_football_starts(api: FetchAPI, time: TimeManagement, competition_id: int) -> list[datetime]:
    played = _svenskfotboll_paginate(api, time, "played-games", competition_id)
    upcoming = _svenskfotboll_paginate(api, time, "upcoming-games", competition_id)
    return played + upcoming


def _iihf_starts(api: FetchAPI, tournament_id: int) -> list[datetime]:
    starts: list[datetime] = []
    games = api.get(f"https://realtime.iihf.com/gamestate/GetLatestScoresState/{tournament_id}")
    for g in games:
        dt = _parse_iso(g.get("GameDateTimeUTC", ""))
        if dt:
            starts.append(dt.astimezone(timezone.utc))
    return starts


def _fifa_starts(api: FetchAPI, season_id: str) -> list[datetime]:
    starts: list[datetime] = []
    url = f"https://api.fifa.com/api/v3/calendar/matches?language=en&count=500&idSeason={season_id}"
    data = api.get(url)
    for match in data.get("Results", []):
        dt = _parse_iso(match.get("Date", ""))
        if dt:
            starts.append(dt)
    return starts


def _compute(league_slug: str) -> SeasonStats | None:
    league_key = _slug_to_league_key().get(league_slug)
    if league_key is None:
        return None

    api = FetchAPI()
    tm = TimeManagement()
    helpers = HelpFunctions()

    starts: list[datetime] = []
    regular_count: int | None = None

    if league_key in FootballFilter.LEAGUES:
        starts = _football_starts(api, tm, FootballFilter.LEAGUES[league_key])
    elif league_key in SwedishFootballFilter.LEAGUES:
        starts = _swedish_football_starts(api, tm, SwedishFootballFilter.LEAGUES[league_key])
    elif league_key in IIHFFilter.TOURNAMENTS:
        starts = _iihf_starts(api, IIHFFilter.TOURNAMENTS[league_key])
    elif league_key in FifaFilter.TOURNAMENTS:
        starts = _fifa_starts(api, FifaFilter.TOURNAMENTS[league_key])
    else:
        for leagues in HockeyBasketballFilter.LEAGUES.values():
            if league_key in leagues:
                all_starts, regular_starts = _hockey_basketball_starts(
                    api, helpers, leagues[league_key]["url_slug"]
                )
                starts = all_starts
                regular_count = len(regular_starts) if regular_starts else len(all_starts)
                break

    progressive_knockout = league_slug in _PROGRESSIVE_KNOCKOUT_SLUGS

    if not starts:
        return SeasonStats(
            season_start=None,
            regular_season_count=0,
            published=False,
            progressive_knockout=progressive_knockout,
        )

    return SeasonStats(
        season_start=min(starts),
        regular_season_count=regular_count if regular_count is not None else len(starts),
        published=True,
        progressive_knockout=progressive_knockout,
    )


def get_season_stats(league_slug: str) -> SeasonStats | None:
    cached = _cache.get(league_slug)
    if cached is not MISSING:
        return cached

    result = _compute(league_slug)
    if result is not None:
        _cache.set(league_slug, result)
    return result
