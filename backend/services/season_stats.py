"""Live season overview (start date + regular-season match count), computed
directly from the same external providers backend/tasks/fetcher.py uses.

Why not just read our own DB? The synced Match table only ever holds a rolling
window (recent + upcoming matches — see TimeManagement.is_recent_or_future),
so right after a season ends and before the next one is announced it can look
like "the season has 1 match" when really the full season simply hasn't been
scraped into our window. Querying the providers directly for the whole season
(no recency filter) gives an honest answer, including "not published yet".
"""

import time as time_module
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from tasks.fetcher import (
    FetchAPI,
    FifaFilter,
    FootballFilter,
    HelpFunctions,
    HockeyBasketballFilter,
    IIHFFilter,
    LEAGUE_DISPLAY,
    SwedishFootballFilter,
    TimeManagement,
    slugify,
)

_CACHE_TTL_SECONDS = 6 * 60 * 60  # these calls are expensive (PL: up to 49 requests/league)
_cache: dict[str, tuple[float, "SeasonStats"]] = {}

_PLAYOFF_FRAGMENTS = ("playoff", "slutspel", "kvalspel", "playout")

# Pure knockout cups whose pairings are drawn round-by-round as the competition
# progresses (the next round isn't fixed until the previous one finishes) — so
# unlike a league or a League Phase, there's no fixed "total games this season"
# to report. league-slug based since it's a property of the competition format,
# not something derivable from the fixture data itself.
_PROGRESSIVE_KNOCKOUT_SLUGS = {"fa-cup", "efl-cup"}


class SeasonStats:
    def __init__(
        self,
        season_start: datetime | None,
        regular_season_count: int,
        published: bool,
        progressive_knockout: bool = False,
    ):
        self.season_start = season_start
        self.regular_season_count = regular_season_count
        self.published = published
        self.progressive_knockout = progressive_knockout


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
    """Whole season, no recency filter — matchweeks stop once a week comes back empty."""
    season = time.get_active_season_year("08")
    starts = _football_starts_for_season(api, time, league_id, season)
    season_concluded = bool(starts) and max(starts) < datetime.now(timezone.utc)

    # Providers usually publish next season's fixtures well before our month
    # threshold flips (e.g. the PL releases fixtures in June, ~2 months before
    # the August kickoff) — but not always (UEFA's league-phase draw tends to
    # land later, closer to the actual August/September kickoff). So once the
    # assumed season has concluded, check the next one and prefer it if it's
    # out; if it isn't, report nothing rather than presenting a finished
    # season's dates as if they were still upcoming.
    if not starts or season_concluded:
        next_season = str(int(season) + 1)
        next_starts = _football_starts_for_season(api, time, league_id, next_season)
        if next_starts:
            return next_starts
        if season_concluded:
            return []
    return starts


def _is_playoff_game_type(item: dict) -> bool:
    for key in ("name", "Name", "description", "Description", "seriesName", "typeName"):
        val = item.get(key)
        if isinstance(val, str) and any(frag in val.lower() for frag in _PLAYOFF_FRAGMENTS):
            return True
    return False


def _hockey_basketball_starts(
    api: FetchAPI, helpers: HelpFunctions, url_slug: str
) -> tuple[list[datetime], list[datetime]]:
    """Returns (all starts, regular-season-only starts) — game types are the only
    place this data distinguishes playoffs from the regular season."""
    meta = api.get(f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter")
    season_uuid, series_uuid, game_types = helpers.get_active_season_uuid(meta)

    all_starts: list[datetime] = []
    regular_starts: list[datetime] = []
    for item in game_types:
        is_playoff = _is_playoff_game_type(item)
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
            if not time_el or not time_el.get("datetime"):
                continue
            dt = _parse_iso(time.convert_to_utc(time_el.get("datetime")))
            if dt:
                starts.append(dt)
        next_url = page.get("nextUrl")
    return starts


def _swedish_football_starts(api: FetchAPI, time: TimeManagement, competition_id: int) -> list[datetime]:
    # "upcoming-games" (what the fetcher's calendar sync uses) only ever returns
    # future fixtures — once the season is underway, it can't see the rounds
    # already played, so it can't tell us the true season start. "played-games"
    # is the sibling endpoint with results; combining both gives the whole season.
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
    regular_count: int | None = None  # None → no regular/playoff split for this competition

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
                # If nothing got tagged as regular season (e.g. an unrecognized
                # game-type label), fall back to the total rather than reporting 0.
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
    now = time_module.monotonic()
    cached = _cache.get(league_slug)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    result = _compute(league_slug)
    if result is not None:
        _cache[league_slug] = (now, result)
    return result
