import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from requests.adapters import HTTPAdapter
from sqlmodel import Session, select
from urllib3.util.retry import Retry

from database import engine
from models.models import League, Match, Sport, Team


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# Substrings that indicate a placeholder team name (fixture not yet decided).
_PLACEHOLDER_FRAGMENTS = {
    "winner", "loser", "runner-up", "runner up", "tbd", "tbc",
    "semi-final", "semifinal", "quarter-final", "quarterfinal",
    "to be confirmed", "to be decided",
}


def _is_placeholder(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in _PLACEHOLDER_FRAGMENTS)


# Maps sport string from filters → (db_name, db_slug, icon)
SPORT_META: dict[str, tuple[str, str, str]] = {
    "football":   ("Football",     "football",         "football"),
    "hockey":     ("Hockey",       "hockey",           "hockey"),
    "basketball": ("Basketball",   "basketball",       "basketball"),
}

# Maps raw league key → display name
LEAGUE_DISPLAY: dict[str, str] = {
    "premier_league":           "Premier League",
    "uefa_champions_league":    "UEFA Champions League",
    "uefa_conference_league":   "UEFA Conference League",
    "fa_cup":                   "FA Cup",
    "efl_cup":                  "EFL Cup",
    "uefa_europa_league":       "UEFA Europa League",
    "allsvenskan":              "Allsvenskan",
    "shl":                      "SHL",
    "sdhl":                     "SDHL",
    "sblherrar":                "SBL Herrar",
    "sbldamer":                 "SBL Damer",
    "iihf_world_championship":  "IIHF World Championship",
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
            total=5, read=5, connect=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, url: str) -> dict:
        r = self.session.get(url, headers=self.HEADERS, timeout=(5, 30))
        r.raise_for_status()
        return r.json()


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
        dt = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
        return dt <= datetime.now(timezone.utc)

    def convert_to_utc(self, start_date_and_time: str, time_zone: str | None = None) -> str:
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
        return sport

    def _get_or_create_league(self, league_key: str, sport_id: int) -> League:
        name = LEAGUE_DISPLAY.get(league_key, league_key.replace("_", " ").title())
        slug = slugify(name)  # slug from display name so it matches what the frontend generates
        league = self.session.exec(select(League).where(League.slug == slug)).first()
        if not league:
            league = League(name=name, slug=slug, sport_id=sport_id)
            self.session.add(league)
            self.session.flush()
        return league

    def _get_or_create_team(self, name: str, league_id: int) -> Team:
        team = self.session.exec(
            select(Team).where(Team.name == name, Team.league_id == league_id)
        ).first()
        if not team:
            team = Team(name=name, slug=slugify(name), league_id=league_id)
            self.session.add(team)
            self.session.flush()
        return team

    def save(self, sport_key: str, league_key: str, events: dict) -> None:
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, sport.id)

        expected_external_ids: set[str] = set()

        for event_id, event in events.items():
            if _is_placeholder(event["homeTeam"]) or _is_placeholder(event["awayTeam"]):
                continue
            home_team = self._get_or_create_team(event["homeTeam"], league.id)
            away_team = self._get_or_create_team(event["awayTeam"], league.id)
            start_time = datetime.fromisoformat(event["startDateAndTime"].replace("Z", "+00:00"))

            # Each match stored twice — once per team — so calendar queries stay simple
            for team, ext_suffix in [(home_team, "home"), (away_team, "away")]:
                external_id = f"{event_id}_{ext_suffix}"
                expected_external_ids.add(external_id)
                existing = self.session.exec(
                    select(Match).where(Match.external_id == external_id)
                ).first()
                if existing:
                    existing.home_team = event["homeTeam"]
                    existing.away_team = event["awayTeam"]
                    existing.start_time = start_time
                    self.session.add(existing)
                else:
                    self.session.add(Match(
                        external_id=external_id,
                        team_id=team.id,
                        home_team=event["homeTeam"],
                        away_team=event["awayTeam"],
                        start_time=start_time,
                    ))

        # Reconcile: delete future matches in this league that the source no longer reports.
        # Past matches are left alone — sources stop returning them once played, but we keep history.
        team_ids = [t.id for t in self.session.exec(
            select(Team).where(Team.league_id == league.id)
        ).all()]
        deleted = 0
        if team_ids:
            now = datetime.now(timezone.utc)
            future_matches = self.session.exec(
                select(Match).where(
                    Match.team_id.in_(team_ids),
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
        "premier_league":           8,
        "uefa_champions_league":    5,
        "uefa_conference_league":   1125,
        "fa_cup":                   1,
        "efl_cup":                  2,
        "uefa_europa_league":       6,
    }

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def filter(self):
        season = self.time.get_active_season_year("08")
        for league_key, league_id in self.LEAGUES.items():
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
                    start = self.time.convert_to_utc(match["kickoff"], match["kickoffTimezone"])
                    if self.time.has_date_passed(start):
                        continue
                    event_id = str(match["matchId"])
                    events[event_id] = {
                        "eventId":          event_id,
                        "homeTeam":         match["homeTeam"]["name"],
                        "awayTeam":         match["awayTeam"]["name"],
                        "startDateAndTime": start,
                    }
            self.store.save("football", league_key, events)


class HockeyBasketballFilter:
    LEAGUES = {
        "hockey": {
            "shl":      {"url_slug": "shl"},
            "sdhl":     {"url_slug": "sdhl"},
        },
        "basketball": {
            "sblherrar": {"url_slug": "sblherr"},
            "sbldamer":  {"url_slug": "sbldam"},
        },
    }

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore, helpers: HelpFunctions):
        self.api = api
        self.time = time
        self.store = store
        self.helpers = helpers

    def filter(self):
        season = self.time.get_active_season_year("09")
        for sport_key, leagues in self.LEAGUES.items():
            for league_key, league_data in leagues.items():
                events: dict = {}
                url_slug = league_data["url_slug"]
                meta = self.api.get(f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter")
                season_uuid, series_uuid, game_type_uuid = self.helpers.get_active_season_uuid(meta)

                for game_type in [item["uuid"] for item in game_type_uuid]:
                    url = (
                        f"https://www.{url_slug}.se/api/sports-v2/game-schedule"
                        f"?seasonUuid={season_uuid}&seriesUuid={series_uuid}"
                        f"&gameTypeUuid={game_type}&gamePlace=all&played=all"
                    )
                    match_data = self.api.get(url)
                    for match in match_data["gameInfo"]:
                        if self.time.has_date_passed(match["rawStartDateTime"]):
                            continue
                        if "names" not in match["homeTeamInfo"] or "names" not in match["awayTeamInfo"]:
                            continue
                        event_id = match["uuid"]
                        events[event_id] = {
                            "eventId":          event_id,
                            "homeTeam":         match["homeTeamInfo"]["names"]["full"],
                            "awayTeam":         match["awayTeamInfo"]["names"]["full"],
                            "startDateAndTime": match["rawStartDateTime"],
                        }
                self.store.save(sport_key, league_key, events)


class SwedishFootballFilter:
    BASE_URL = "https://www.svenskfotboll.se"
    LEAGUES = {"allsvenskan": 133348}

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def filter(self):
        season = self.time.get_active_season_year("03")
        for league_key, competition_id in self.LEAGUES.items():
            events: dict = {}
            next_url = f"/api/upcoming-games/?competitionId={competition_id}&from=0"
            while next_url:
                page = self.api.get(self.BASE_URL + next_url)
                soup = BeautifulSoup(page["data"], "html.parser")
                for match in soup.select(".match-list__match"):
                    home = match.select_one(".match-list__home .match-list__team-name").text.strip()
                    away = match.select_one(".match-list__away .match-list__team-name").text.strip()
                    start = self.time.convert_to_utc(match.select_one("time").get("datetime"))
                    href = match.select_one(".match-list__link").get("href")
                    event_id = parse_qs(urlparse(href).query).get("fmid", [None])[0]
                    if self.time.has_date_passed(start) or not event_id:
                        continue
                    events[str(event_id)] = {
                        "eventId":          str(event_id),
                        "homeTeam":         home,
                        "awayTeam":         away,
                        "startDateAndTime": start,
                    }
                next_url = page.get("nextUrl")
            self.store.save("football", league_key, events)


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
            games = self.api.get(f"https://realtime.iihf.com/gamestate/GetLatestScoresState/{tournament_id}")
            for g in games:
                utc_str = (
                    datetime.fromisoformat(g["GameDateTimeUTC"].replace("Z", "+00:00"))
                    .astimezone(timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                if self.time.has_date_passed(utc_str):
                    continue
                home_code = g["HomeTeam"]["TeamCode"]
                away_code = g["GuestTeam"]["TeamCode"]
                event_id = str(g.get("GameId", f"{home_code}v{away_code}{utc_str[:10]}"))
                events[event_id] = {
                    "eventId":          event_id,
                    "homeTeam":         self._team_name(home_code),
                    "awayTeam":         self._team_name(away_code),
                    "startDateAndTime": utc_str,
                }
            self.store.save("hockey", tournament_key, events)


# ── Fetcher state (readable by health endpoint) ───────────────────────────────

fetcher_state: dict = {
    "last_run": None,       # ISO string of last successful run
    "last_error": None,     # error message from last failed run
    "status": "pending",    # "pending" | "ok" | "error"
}


# ── Entry point (called by scheduler) ────────────────────────────────────────

def run_fetch() -> None:
    print(f"[fetcher] starting at {datetime.now(timezone.utc).isoformat()}")
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

        fetcher_state["status"] = "ok"
        fetcher_state["last_run"] = datetime.now(timezone.utc).isoformat()
        fetcher_state["last_error"] = None
        print("[fetcher] done")
    except Exception as e:
        fetcher_state["status"] = "error"
        fetcher_state["last_error"] = str(e)
        print(f"[fetcher] error: {e}")
