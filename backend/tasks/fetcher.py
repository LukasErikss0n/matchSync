import re
import time as time_module
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import requests
import resend
from bs4 import BeautifulSoup, Tag
from config import ALERT_EMAIL, RESEND_API_KEY
from database import engine
from dateutil.parser import parse
from models.models import League, Match, Sport, Team
from requests.adapters import HTTPAdapter
from services.crest_color import analyze_crest
from sqlmodel import Session, col, select
from urllib3.util.retry import Retry

# ── Helpers ───────────────────────────────────────────────────────────────────


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# Substrings that indicate a placeholder team name (fixture not yet decided).
_PLACEHOLDER_FRAGMENTS = {
    "winner",
    "loser",
    "runner-up",
    "runner up",
    "tbd",
    "tbc",
    "semi-final",
    "semifinal",
    "quarter-final",
    "quarterfinal",
    "to be confirmed",
    "to be decided",
}


def _to_int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _is_placeholder(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in _PLACEHOLDER_FRAGMENTS)


def _pk(row: Sport | League | Team) -> int:
    """Primary key of a persisted row. Every row DBStore handles comes from a
    query or has been flush()ed, so id is always set — this just states that
    where the type checker can see it."""
    assert row.id is not None
    return row.id


def _attr_str(tag: Tag | None, name: str) -> str | None:
    """A tag attribute as a plain string. BeautifulSoup's .get() can also
    return a list (multi-valued attributes) or None (missing tag/attribute) —
    both mean "no usable value" for our purposes."""
    if tag is None:
        return None
    val = tag.get(name)
    return val if isinstance(val, str) else None


# Shared with services/season_stats.py (regular-season match counting) and
# services/standings_local.py (excluding playoff games from the table) — the
# hockey/basketball game-schedule feed mixes regular-season and playoff games
# with no other way to tell them apart than this game-type label.
PLAYOFF_FRAGMENTS = ("playoff", "slutspel", "kvalspel", "playout")


def is_playoff_game_type(item: dict) -> bool:
    for key in ("name", "Name", "description", "Description", "seriesName", "typeName"):
        val = item.get(key)
        if isinstance(val, str) and any(frag in val.lower() for frag in PLAYOFF_FRAGMENTS):
            return True
    return False


# Maps sport string from filters → (db_name, db_slug, icon)
SPORT_META: dict[str, tuple[str, str, str]] = {
    "football": ("Football", "football", "football"),
    "hockey": ("Hockey", "hockey", "hockey"),
    "basketball": ("Basketball", "basketball", "basketball"),
    "motorsport": ("Motorsport", "motorsport", "flag"),
}

# Maps raw league key → display name
LEAGUE_DISPLAY: dict[str, str] = {
    "premier_league": "Premier League",
    "uefa_champions_league": "UEFA Champions League",
    "uefa_conference_league": "UEFA Conference League",
    "fa_cup": "FA Cup",
    "efl_cup": "EFL Cup",
    "uefa_europa_league": "UEFA Europa League",
    "allsvenskan": "Allsvenskan",
    "shl": "SHL",
    "sdhl": "SDHL",
    "sblherrar": "SBL Herrar",
    "sbldamer": "SBL Damer",
    "iihf_world_championship": "IIHF World Championship",
    "fifa_world_cup_2026": "FIFA World Cup 2026",
    "f1": "Formula 1",
}


# ── HTTP client ───────────────────────────────────────────────────────────────


class FetchAPI:
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Connection": "keep-alive",
    }

    def __init__(self):
        self.session = requests.Session()
        retry = Retry(
            total=5,
            read=5,
            connect=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, url: str) -> dict:
        r = self.session.get(url, headers=self.HEADERS, timeout=(5, 30))
        r.raise_for_status()
        return r.json()


# Premier League's own date-based season cutover (used for fixtures/standings,
# see FootballFilter.SEASON_START_MONTH) flips well before their badge CDN
# actually publishes the new season's crest folder — historically the gap has
# been ~2 weeks around each kickoff. Requesting the not-yet-published folder
# 502s for every single team, so probe for it and fall back to last season's
# folder (which keeps 200-ing fine) until the new one is confirmed live.
# Cached with a short TTL so it picks up the real folder soon after PL
# publishes it, without re-probing on every ~30 min fetcher run.
_PL_BADGE_YEAR_CACHE: dict[int, tuple[float, str]] = {}
_PL_BADGE_YEAR_CACHE_TTL_SECONDS = 3 * 60 * 60


def _resolve_pl_badge_year() -> str:
    now = datetime.now()
    candidate_year = now.year if now.month >= 8 else now.year - 1

    cached = _PL_BADGE_YEAR_CACHE.get(candidate_year)
    now_monotonic = time_module.monotonic()
    if cached and now_monotonic - cached[0] < _PL_BADGE_YEAR_CACHE_TTL_SECONDS:
        return cached[1]

    candidate = str(candidate_year)[-2:]
    probe_url = f"https://resources.premierleague.com/premierleague{candidate}/badges-alt/50/1.png"
    try:
        resp = requests.head(probe_url, headers=FetchAPI.HEADERS, timeout=(3, 5))
        yr = candidate if resp.status_code == 200 else str(candidate_year - 1)[-2:]
    except requests.RequestException:
        yr = str(candidate_year - 1)[-2:]

    _PL_BADGE_YEAR_CACHE[candidate_year] = (now_monotonic, yr)
    return yr


# ── Time helpers ──────────────────────────────────────────────────────────────


class TimeManagement:
    TIMEZONE_MAP = {"BST": "Europe/London", "GMT": "Europe/London"}

    def get_active_season_year(self, start_month: str) -> str:
        now = datetime.now()
        season = str(now.year - 1)
        if now.strftime("%m") >= start_month:
            season = str(now.year)
        return season

    def has_date_passed(self, date_utc: str) -> bool:
        try:
            dt = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
        except ValueError:
            return (
                True  # unparseable date (e.g. placeholder year 0001) — skip the event
            )
        return dt <= datetime.now(timezone.utc)

    RESULTS_WINDOW_DAYS = 10

    def is_recent_or_future(self, date_utc: str) -> bool:
        """True for upcoming matches and ones played within RESULTS_WINDOW_DAYS."""
        try:
            dt = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
        except ValueError:
            return False
        return dt >= datetime.now(timezone.utc) - timedelta(
            days=self.RESULTS_WINDOW_DAYS
        )

    def convert_to_utc(
        self, start_date_and_time: str, time_zone: str | None = None
    ) -> str:
        dt = parse(start_date_and_time)
        if dt.tzinfo is None:
            tz_name = self.TIMEZONE_MAP.get(time_zone) if time_zone else None
            if not tz_name:
                raise ValueError(f"Unknown timezone: {time_zone}")
            dt = dt.replace(tzinfo=ZoneInfo(tz_name))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Database store ────────────────────────────────────────────────────────────


class DBStore:
    """Replaces the JSON-file Store — writes events directly to Postgres."""

    def __init__(self, session: Session):
        self.session = session

    def _get_or_create_sport(self, sport_key: str) -> Sport:
        name, slug, icon = SPORT_META[sport_key]
        sport = self.session.exec(select(Sport).where(Sport.slug == slug)).first()
        if not sport:
            sport = Sport(name=name, slug=slug, icon=icon)
            self.session.add(sport)
            self.session.flush()
        elif sport.icon != icon:
            # Keeps an existing row's icon in sync with SPORT_META — without
            # this, changing an icon here would never reach prod's already-
            # created row (motorsport's car→flag fix needed exactly this).
            sport.icon = icon
            self.session.add(sport)
        return sport

    def _get_or_create_league(self, league_key: str, sport_id: int) -> League:
        name = LEAGUE_DISPLAY.get(league_key, league_key.replace("_", " ").title())
        slug = slugify(
            name
        )  # slug from display name so it matches what the frontend generates
        league = self.session.exec(select(League).where(League.slug == slug)).first()
        if not league:
            league = League(name=name, slug=slug, sport_id=sport_id)
            self.session.add(league)
            self.session.flush()
        return league

    def _get_or_create_team(
        self, name: str, league_id: int, icon: str | None = None
    ) -> Team:
        team = self.session.exec(
            select(Team).where(Team.name == name, Team.league_id == league_id)
        ).first()
        if not team:
            team = Team(name=name, slug=slugify(name), league_id=league_id, icon=icon)
            self.session.add(team)
            self.session.flush()
        elif icon and team.icon != icon:
            # Backfill / refresh the logo once a source starts providing it
            team.icon = icon
            team.color = None
            team.icon_data = None  # re-derived from the new crest by backfill_team_colors
            self.session.add(team)
        return team

    def backfill_icons(
        self, sport_key: str, league_key: str, icons: dict[str, str]
    ) -> None:
        """Update team icons from ALL API games regardless of match date."""
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, _pk(sport))
        for name, icon in icons.items():
            team = self.session.exec(
                select(Team).where(Team.name == name, Team.league_id == league.id)
            ).first()
            if team and team.icon != icon:
                team.icon = icon
                team.color = None
                team.icon_data = None
                self.session.add(team)
        self.session.commit()

    def backfill_sport_icons(self, sport_slug: str, icons: dict[str, str]) -> None:
        """Update icons for all teams in a sport by name, across every league."""
        sport = self.session.exec(select(Sport).where(Sport.slug == sport_slug)).first()
        if not sport:
            return
        league_ids = [
            l.id for l in self.session.exec(
                select(League).where(League.sport_id == sport.id)
            ).all()
        ]
        if not league_ids:
            return
        teams = self.session.exec(
            select(Team).where(col(Team.league_id).in_(league_ids))
        ).all()
        for team in teams:
            icon = icons.get(team.name)
            if icon and team.icon != icon:
                team.icon = icon
                team.color = None
                team.icon_data = None
                self.session.add(team)
        self.session.commit()

    def backfill_team_colors(self) -> None:
        """Derive the primary crest colour and a trimmed crest for teams that
        don't have them yet.

        Only touches teams whose colour is missing (new team, or icon changed
        since the last run), so a steady-state run downloads nothing.
        """
        teams = self.session.exec(
            select(Team).where(col(Team.icon).is_not(None), col(Team.color).is_(None))
        ).all()
        if not teams:
            return
        filled = 0
        for team in teams:
            if not team.icon:  # excluded by the query; restated for the type checker
                continue
            color, cropped = analyze_crest(team.icon)
            if color:
                team.color = color
                team.icon_data = cropped
                self.session.add(team)
                filled += 1
        self.session.commit()
        print(f"[crest-colors] derived {filled}/{len(teams)} team colours")

    def save(self, sport_key: str, league_key: str, events: dict) -> None:
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, _pk(sport))

        expected_external_ids: set[str] = set()

        for event_id, event in events.items():
            if _is_placeholder(event["homeTeam"]) or _is_placeholder(event["awayTeam"]):
                continue
            try:
                start_time = datetime.fromisoformat(
                    event["startDateAndTime"].replace("Z", "+00:00")
                )
            except ValueError:
                continue
            home_team = self._get_or_create_team(
                event["homeTeam"], _pk(league), event.get("homeIcon")
            )
            away_team = self._get_or_create_team(
                event["awayTeam"], _pk(league), event.get("awayIcon")
            )

            home_score = _to_int(event.get("homeScore"))
            away_score = _to_int(event.get("awayScore"))
            is_playoff = bool(event.get("isPlayoff", False))
            overtime = bool(event.get("overtime", False))
            shootout = bool(event.get("shootout", False))

            # Each match stored twice — once per team — so calendar queries stay simple.
            # A third "extra" perspective is opt-in (only F1Filter sets it, for a
            # season-long pseudo-team so users can subscribe to every session at
            # once instead of picking one Grand Prix or session type).
            perspectives = [(home_team, "home"), (away_team, "away")]
            extra_name = event.get("extraTeam")
            if extra_name:
                extra_team = self._get_or_create_team(extra_name, _pk(league), event.get("extraIcon"))
                perspectives.append((extra_team, "extra"))

            for team, ext_suffix in perspectives:
                external_id = f"{event_id}_{ext_suffix}"
                expected_external_ids.add(external_id)
                existing = self.session.exec(
                    select(Match).where(Match.external_id == external_id)
                ).first()
                if existing:
                    existing.team_id = _pk(team)
                    existing.home_team = event["homeTeam"]
                    existing.away_team = event["awayTeam"]
                    existing.start_time = start_time
                    existing.home_score = home_score
                    existing.away_score = away_score
                    existing.is_playoff = is_playoff
                    existing.overtime = overtime
                    existing.shootout = shootout
                    self.session.add(existing)
                else:
                    self.session.add(
                        Match(
                            external_id=external_id,
                            team_id=_pk(team),
                            home_team=event["homeTeam"],
                            away_team=event["awayTeam"],
                            start_time=start_time,
                            home_score=home_score,
                            away_score=away_score,
                            is_playoff=is_playoff,
                            overtime=overtime,
                            shootout=shootout,
                        )
                    )

        team_ids = [
            _pk(t)
            for t in self.session.exec(
                select(Team).where(Team.league_id == league.id)
            ).all()
        ]
        deleted = 0
        if team_ids:
            now = datetime.now(timezone.utc)
            future_matches = self.session.exec(
                select(Match).where(
                    col(Match.team_id).in_(team_ids),
                    Match.start_time > now,
                )
            ).all()
            for m in future_matches:
                if m.external_id not in expected_external_ids:
                    self.session.delete(m)
                    deleted += 1

        self.session.commit()
        print(f"Saved {league_key} → {len(events)} events (removed {deleted} stale)")


# ── Filters (fetching logic unchanged, output goes to DBStore) ────────────────


class HelpFunctions:
    def get_active_season_uuid(self, meta: dict):
        return (
            meta["defaultSsgtFilter"]["season"],
            meta["defaultSsgtFilter"]["series"],
            meta["gameType"],
        )


class FootballFilter:
    LEAGUES = {
        "premier_league": 8,
        "uefa_champions_league": 5,
        "uefa_conference_league": 1125,
        "fa_cup": 1,
        "efl_cup": 2,
        "uefa_europa_league": 6,
    }
    # Also read by services/standings_local.py to draw the season-cutoff line
    # — keep in sync with the get_active_season_year() call in filter() below.
    SEASON_START_MONTH = 8

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _badge_url(self, team: dict) -> str | None:
        team_id = team.get("id")
        if not team_id:
            return None
        yr = _resolve_pl_badge_year()
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
                    "homeIcon":         self._badge_url(match["homeTeam"]),
                    "awayIcon":         self._badge_url(match["awayTeam"]),
                    "homeScore":        match["homeTeam"].get("score"),
                    "awayScore":        match["awayTeam"].get("score"),
                }
        return events

    def filter(self, full_history: bool = False, league_keys: set[str] | None = None):
        """`full_history=True` ignores the recency filter entirely — used by
        scripts/backfill_full_history.py to pull a whole season's results.
        `league_keys` restricts which leagues to sync (also backfill-only)."""
        season = self.time.get_active_season_year(f"{self.SEASON_START_MONTH:02d}")
        for league_key, league_id in self.LEAGUES.items():
            if league_keys is not None and league_key not in league_keys:
                continue
            events = self._fetch_season(league_id, season, full_history=full_history)
            if full_history:
                # full_history means `events` is never empty for an already-
                # completed season (that's the whole point), so the "fetch
                # next season if this one's empty" fallback below would never
                # fire — but we still want next season's fixtures once they're
                # published, so fetch both and merge rather than either/or.
                next_season = str(int(season) + 1)
                next_events = self._fetch_season(league_id, next_season, full_history=full_history)
                events = {**events, **next_events}
            elif not events:
                # Providers usually publish next season's full fixture list well
                # before our month-threshold flips (e.g. the PL releases fixtures
                # in June, ~2 months before the August kickoff) — if the season we
                # assumed has nothing recent/upcoming, the next one may already be out.
                next_season = str(int(season) + 1)
                events = self._fetch_season(league_id, next_season, full_history=full_history)
            self.store.save("football", league_key, events)


class HockeyBasketballFilter:
    LEAGUES = {
        "hockey": {
            "shl": {"url_slug": "shl"},
            "sdhl": {"url_slug": "sdhl"},
        },
        "basketball": {
            "sblherrar": {"url_slug": "sblherr"},
            "sbldamer": {"url_slug": "sbldam"},
        },
    }

    def __init__(
        self,
        api: FetchAPI,
        time: TimeManagement,
        store: DBStore,
        helpers: HelpFunctions,
    ):
        self.api = api
        self.time = time
        self.store = store
        self.helpers = helpers

    def filter(self, full_history: bool = False, league_keys: set[str] | None = None):
        """`full_history=True` ignores the recency filter entirely — used by
        scripts/backfill_full_history.py to pull a whole season's results.
        `league_keys` restricts which leagues to sync (also backfill-only)."""
        season = self.time.get_active_season_year("09")
        for sport_key, leagues in self.LEAGUES.items():
            for league_key, league_data in leagues.items():
                if league_keys is not None and league_key not in league_keys:
                    continue
                events: dict = {}
                url_slug = league_data["url_slug"]
                meta = self.api.get(
                    f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter"
                )
                season_uuid, series_uuid, game_type_uuid = (
                    self.helpers.get_active_season_uuid(meta)
                )

                all_icons: dict[str, str] = {}
                for game_type_item in game_type_uuid:
                    game_type = game_type_item["uuid"]
                    is_playoff = is_playoff_game_type(game_type_item)
                    url = (
                        f"https://www.{url_slug}.se/api/sports-v2/game-schedule"
                        f"?seasonUuid={season_uuid}&seriesUuid={series_uuid}"
                        f"&gameTypeUuid={game_type}&gamePlace=all&played=all"
                    )
                    match_data = self.api.get(url)
                    for match in match_data["gameInfo"]:
                        if (
                            "names" not in match["homeTeamInfo"]
                            or "names" not in match["awayTeamInfo"]
                        ):
                            continue
                        # Collect icons from every game regardless of date so logos
                        # are backfilled even when the whole season is in the past.
                        for info in [match["homeTeamInfo"], match["awayTeamInfo"]]:
                            icon = info.get("icon")
                            if icon:
                                all_icons[info["names"]["full"]] = icon

                        if not full_history and not self.time.is_recent_or_future(match["rawStartDateTime"]):
                            continue
                        event_id = match["uuid"]
                        events[event_id] = {
                            "eventId": event_id,
                            "homeTeam": match["homeTeamInfo"]["names"]["full"],
                            "awayTeam": match["awayTeamInfo"]["names"]["full"],
                            "startDateAndTime": match["rawStartDateTime"],
                            "homeIcon": match["homeTeamInfo"].get("icon"),
                            "awayIcon": match["awayTeamInfo"].get("icon"),
                            "homeScore": match["homeTeamInfo"].get("score"),
                            "awayScore": match["awayTeamInfo"].get("score"),
                            "isPlayoff": is_playoff,
                            "overtime": bool(match.get("overtime")),
                            "shootout": bool(match.get("shootout")),
                        }
                if all_icons:
                    self.store.backfill_icons(sport_key, league_key, all_icons)
                self.store.save(sport_key, league_key, events)


class SwedishFootballFilter:
    BASE_URL = "https://www.svenskfotboll.se"
    LEAGUES = {"allsvenskan": 133348}
    # Also read by services/standings_local.py to draw the season-cutoff line
    # — keep in sync with the get_active_season_year() call in filter() below.
    SEASON_START_MONTH = 3

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def filter(self):
        season = self.time.get_active_season_year(f"{self.SEASON_START_MONTH:02d}")
        for league_key, competition_id in self.LEAGUES.items():
            events: dict = {}
            self._collect(
                events, f"/api/upcoming-games/?competitionId={competition_id}&from=0"
            )
            # Separate endpoint for finished matches — this is where scores live;
            # upcoming-games never carries a result even for matches that have
            # since been played. Ordered most-recent-first, so once a match
            # falls outside the results window everything after it is older
            # still — safe to stop paginating instead of walking full history.
            self._collect(
                events,
                f"/api/played-games/?competitionId={competition_id}&from=0",
                stop_when_old=True,
            )
            self.store.save("football", league_key, events)

    def _collect(
        self,
        events: dict,
        start_url: str,
        stop_when_old: bool = False,
        full_history: bool = False,
    ) -> None:
        """`full_history=True` ignores the recency filter entirely — used by
        the one-off backfill script (scripts/backfill_full_history.py) to pull
        a whole season's results, since the regular sync only ever needs the
        last RESULTS_WINDOW_DAYS."""
        next_url: str | None = start_url
        while next_url:
            page = self.api.get(self.BASE_URL + next_url)
            soup = BeautifulSoup(page["data"], "html.parser")
            hit_old = False
            for match in soup.select(".match-list__match"):
                home_el = match.select_one(".match-list__home .match-list__team-name")
                away_el = match.select_one(".match-list__away .match-list__team-name")
                start_attr = _attr_str(match.select_one("time"), "datetime")
                href = _attr_str(match.select_one(".match-list__link"), "href")
                if home_el is None or away_el is None or not start_attr or not href:
                    # Row without the expected markup (site tweak, ad slot…) —
                    # skip it rather than crash the whole fetch run.
                    continue
                home = home_el.text.strip()
                away = away_el.text.strip()
                home_icon = _attr_str(
                    match.select_one(".match-list__home .team-logo__img"), "src"
                )
                away_icon = _attr_str(
                    match.select_one(".match-list__away .team-logo__img"), "src"
                )
                start = self.time.convert_to_utc(start_attr)
                event_id = parse_qs(urlparse(href).query).get("fmid", [None])[0]
                if not event_id:
                    continue
                if not full_history and not self.time.is_recent_or_future(start):
                    if stop_when_old:
                        hit_old = True
                        break
                    continue

                event = events.setdefault(
                    str(event_id),
                    {
                        "eventId":          str(event_id),
                        "homeTeam":         home,
                        "awayTeam":         away,
                        "startDateAndTime": start,
                        "homeIcon":         home_icon,
                        "awayIcon":         away_icon,
                    },
                )
                home_score_el = match.select_one(".match-list__home .match-list__score")
                away_score_el = match.select_one(".match-list__away .match-list__score")
                if home_score_el is not None:
                    event["homeScore"] = home_score_el.text.strip()
                if away_score_el is not None:
                    event["awayScore"] = away_score_el.text.strip()
            next_url = None if hit_old else page.get("nextUrl")


class IIHFFilter:
    TOURNAMENTS = {
        "iihf_world_championship": 969,
    }

    TEAM_NAMES: dict[str, str] = {
        "AUT": "Austria",
        "BLR": "Belarus",
        "BEL": "Belgium",
        "CAN": "Canada",
        "CZE": "Czechia",
        "DEN": "Denmark",
        "EST": "Estonia",
        "FIN": "Finland",
        "FRA": "France",
        "GBR": "Great Britain",
        "GER": "Germany",
        "HUN": "Hungary",
        "ITA": "Italy",
        "JPN": "Japan",
        "KAZ": "Kazakhstan",
        "KOR": "South Korea",
        "LAT": "Latvia",
        "LTU": "Lithuania",
        "NED": "Netherlands",
        "NOR": "Norway",
        "POL": "Poland",
        "ROM": "Romania",
        "SVK": "Slovakia",
        "SLO": "Slovenia",
        "SUI": "Switzerland",
        "SWE": "Sweden",
        "UKR": "Ukraine",
        "USA": "United States",
    }

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _team_name(self, code: str) -> str:
        return self.TEAM_NAMES.get(code, code)

    def filter(self):
        season = self.time.get_active_season_year("05")
        for tournament_key, tournament_id in self.TOURNAMENTS.items():
            events: dict = {}
            games = self.api.get(
                f"https://realtime.iihf.com/gamestate/GetLatestScoresState/{tournament_id}"
            )
            for g in games:
                utc_str = (
                    datetime.fromisoformat(g["GameDateTimeUTC"].replace("Z", "+00:00"))
                    .astimezone(timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                if not self.time.is_recent_or_future(utc_str):
                    continue
                home_code = g["HomeTeam"]["TeamCode"]
                away_code = g["GuestTeam"]["TeamCode"]
                event_id = str(
                    g.get("GameId", f"{home_code}v{away_code}{utc_str[:10]}")
                )
                events[event_id] = {
                    "eventId": event_id,
                    "homeTeam": self._team_name(home_code),
                    "awayTeam": self._team_name(away_code),
                    "startDateAndTime": utc_str,
                    # Live-state feed carries scores (and sometimes a logo) — all optional
                    "homeIcon": g["HomeTeam"].get("Logo"),
                    "awayIcon": g["GuestTeam"].get("Logo"),
                    "homeScore": g["HomeTeam"].get("Score"),
                    "awayScore": g["GuestTeam"].get("Score"),
                }
            self.store.save("hockey", tournament_key, events)


class FifaFilter:
    TOURNAMENTS = {
        "fifa_world_cup_2026": "285023",
    }

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _team_name(self, team: dict) -> str | None:
        names = team.get("TeamName") or []
        return names[0]["Description"] if names else None

    def _picture_url(self, team: dict) -> str | None:
        # FIFA crest URLs carry {format} (shape: "sq") and {size} (1-4, 4 = largest).
        url = team.get("PictureUrl")
        if not url:
            return None
        return url.replace("{format}", "sq").replace("{size}", "4")

    def filter(self):
        for tournament_key, season_id in self.TOURNAMENTS.items():
            events: dict = {}
            url = (
                "https://api.fifa.com/api/v3/calendar/matches"
                f"?language=en&count=500&idSeason={season_id}"
            )
            data = self.api.get(url)
            for match in data.get("Results", []):
                if not self.time.is_recent_or_future(match["Date"]):
                    continue
                home = match.get("Home") or {}
                away = match.get("Away") or {}
                home_name = self._team_name(home)
                away_name = self._team_name(away)
                if not home_name or not away_name:
                    continue
                event_id = str(match["IdMatch"])
                events[event_id] = {
                    "eventId": event_id,
                    "homeTeam": home_name,
                    "awayTeam": away_name,
                    "startDateAndTime": match["Date"],
                    "homeIcon": self._picture_url(home),
                    "awayIcon": self._picture_url(away),
                    "homeScore": home.get("Score"),
                    "awayScore": away.get("Score"),
                }
            self.store.save("football", tournament_key, events)


class F1Filter:
    """Formula 1 via OpenF1 (api.openf1.org, free/unauthenticated). F1 doesn't
    have a two-competitor "match" like the other sports here — every session
    is one field of ~20 drivers — so this reuses the home/away Match shape
    loosely: "home_team" is the Grand Prix (e.g. "Australian Grand Prix"),
    "away_team" is the session (e.g. "Practice 1", "Qualifying", "Race").
    That gives the team-picker two useful, genuinely distinct things to
    subscribe by — a specific Grand Prix weekend, or a session type across
    the whole season (e.g. every "Race") — without needing driver/constructor
    data this app has nowhere else to use. Every session also gets a third
    "Formula 1" pseudo-team (via DBStore.save's optional extraTeam) — the only
    one actually exposed in the team picker (see routers/leagues.py's
    TEAM_SEARCH_SINGLE_PICKABLE) — for subscribing to the entire calendar
    at once instead of one Grand Prix or session type."""

    BASE_URL = "https://api.openf1.org/v1"
    LEAGUES = {"f1": None}
    # Stable public asset (Wikimedia Commons) — OpenF1 doesn't serve a series logo.
    LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg"
    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _get_list(self, url: str) -> list:
        # OpenF1 404s (rather than returning []) for a year/meeting it has no
        # data for yet (e.g. next season, before the calendar's published).
        try:
            data = self.api.get(url)
        except requests.HTTPError:
            return []
        return data if isinstance(data, list) else []

    def filter(self, full_history: bool = False):
        """`full_history=True` ignores the recency filter entirely — used by
        scripts/backfill_full_history.py. OpenF1 doesn't expose a round
        number, so the frontend derives "Round N" by counting meetings in
        chronological order from whatever's in our DB — without a full-season
        backfill that count starts from whatever the rolling window happens
        to still have, not the real round 1.

        Only the current calendar year — unlike Premier League etc., an F1
        season doesn't cross a year boundary, so there's no "next season"
        lookahead needed here. Pulling in next year's meetings too (once
        published) would mix two seasons into the same chronological round
        count instead of resetting at the new season's round 1."""
        year = datetime.now().year
        events: dict = {}
        meetings = self._get_list(f"{self.BASE_URL}/meetings?year={year}")
        for meeting in meetings:
            name = meeting.get("meeting_name")
            meeting_key = meeting.get("meeting_key")
            # is_cancelled catches dropped/rescheduled-away meetings (e.g. the
            # 2026 Bahrain GP at Sakhir). It's per-meeting, not per-name — a
            # cancelled Grand Prix that gets rescheduled elsewhere reuses the
            # same meeting_name for its new meeting, which is NOT cancelled,
            # so a name-based exclusion would wrongly drop that one too.
            if (
                not name
                or meeting_key is None
                or "testing" in name.lower()
                or meeting.get("is_cancelled")
            ):
                continue
            sessions = self._get_list(f"{self.BASE_URL}/sessions?meeting_key={meeting_key}")
            for session in sessions:
                start = session.get("date_start")
                session_key = session.get("session_key")
                if not start or session_key is None:
                    continue
                if not full_history and not self.time.is_recent_or_future(start):
                    continue
                event_id = str(session_key)
                events[event_id] = {
                    "eventId": event_id,
                    "homeTeam": name,
                    "awayTeam": session.get("session_name") or session.get("session_type") or "Session",
                    "startDateAndTime": start,
                    "homeIcon": meeting.get("country_flag"),
                    # Third pseudo-team every session also belongs to, so
                    # subscribing to it gives the whole season at once
                    # instead of one Grand Prix or one session type.
                    "extraTeam": "Formula 1",
                    "extraIcon": self.LOGO_URL,
                }
        self.store.save("motorsport", "f1", events)


class FootballIconsFetcher:
    """Fetches Premier League team crests via the FPL bootstrap API and stores
    them for every football team (PL, UCL, UEL, etc.) matched by name."""

    FPL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

    # FPL short name → full name used by the PL schedule API
    NAME_MAP: dict[str, str] = {
        "Man City":       "Manchester City",
        "Man Utd":        "Manchester United",
        "Spurs":          "Tottenham Hotspur",
        "Wolves":         "Wolverhampton Wanderers",
        "Newcastle":      "Newcastle United",
        "West Ham":       "West Ham United",
        "Nott'm Forest":  "Nottingham Forest",
        "Brighton":       "Brighton and Hove Albion",
        "Bournemouth":    "Bournemouth",
        "Leicester":      "Leicester City",
        "Ipswich":        "Ipswich Town",
        "Leeds":          "Leeds United",
        "Luton":          "Luton Town",
        "Sheffield Utd":  "Sheffield United",
        "Middlesbrough":  "Middlesbrough",
        "Sunderland":     "Sunderland",
    }

    def __init__(self, api: FetchAPI, store: DBStore):
        self.api = api
        self.store = store

    def _badge_url(self, code: int) -> str:
        yr = _resolve_pl_badge_year()
        return f"https://resources.premierleague.com/premierleague{yr}/badges-alt/{code}.svg"

    def filter(self):
        data = self.api.get(self.FPL_URL)
        icons: dict[str, str] = {}
        for team in data.get("teams", []):
            code = team.get("code")
            fpl_name = team.get("name")
            if not isinstance(code, int) or not isinstance(fpl_name, str) or not fpl_name:
                continue
            db_name = self.NAME_MAP.get(fpl_name, fpl_name)
            icons[db_name] = self._badge_url(code)

        if icons:
            self.store.backfill_sport_icons("football", icons)
            print(f"[football-icons] updated {len(icons)} team crests")


# ── Fetcher state (readable by health endpoint) ───────────────────────────────

fetcher_state: dict = {
    "last_run": None,  # ISO string of last successful run
    "last_error": None,  # error message from last failed run
    "status": "pending",  # "pending" | "ok" | "error"
}


def _send_error_email(error: str) -> None:
    if not RESEND_API_KEY or not ALERT_EMAIL:
        print("[fetcher] email not configured, skipping alert")
        return
    try:
        resend.api_key = RESEND_API_KEY
        resp = resend.Emails.send(
            {
                "from": "alerts@matchcalender.com",
                "to": ALERT_EMAIL,
                "subject": "MatchCalender fetcher error",
                "text": f"MatchCalender fetcher failed at {datetime.now(_LOCAL_TZ).isoformat()}\n\nError:\n{error}",
            }
        )
        # Log the id Resend hands back rather than just "sent": accepting the
        # request only means it's queued, so a message can still bounce or be
        # junked afterwards. The id is what makes it findable in the Resend
        # dashboard when an alert doesn't turn up.
        email_id = resp.get("id") if isinstance(resp, dict) else None
        print(f"[fetcher] error alert queued with Resend (id={email_id or 'unknown'})")
    except Exception as e:
        print(f"[fetcher] failed to send alert email: {e}")


# ── Entry point (called by scheduler) ────────────────────────────────────────

_LOCAL_TZ = ZoneInfo("Europe/Stockholm")


def run_fetch() -> None:
    print(f"[fetcher] starting at {datetime.now(_LOCAL_TZ).isoformat()}")
    api = FetchAPI()
    time = TimeManagement()
    helpers = HelpFunctions()

    try:
        with Session(engine) as session:
            store = DBStore(session)
            FootballFilter(api, time, store).filter()
            HockeyBasketballFilter(api, time, store, helpers).filter()
            SwedishFootballFilter(api, time, store).filter()
            IIHFFilter(api, time, store).filter()
            FifaFilter(api, time, store).filter()
            F1Filter(api, time, store).filter()
            FootballIconsFetcher(api, store).filter()
            # Last, so every icon written above gets a colour in the same run.
            store.backfill_team_colors()

        fetcher_state["status"] = "ok"
        fetcher_state["last_run"] = datetime.now(_LOCAL_TZ).isoformat()
        fetcher_state["last_error"] = None
        print("[fetcher] done")
    except Exception as e:
        was_ok = fetcher_state["status"] != "error"
        fetcher_state["status"] = "error"
        fetcher_state["last_error"] = str(e)
        print(f"[fetcher] error: {e}")
        if was_ok:
            _send_error_email(str(e))
