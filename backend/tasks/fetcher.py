import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import requests
import resend
from bs4 import BeautifulSoup
from config import ALERT_EMAIL, RESEND_API_KEY
from database import engine
from dateutil.parser import parse
from models.models import League, Match, Sport, Team
from requests.adapters import HTTPAdapter
from sqlmodel import Session, select
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


def _to_int(val: object) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _is_placeholder(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in _PLACEHOLDER_FRAGMENTS)


# Maps sport string from filters → (db_name, db_slug, icon)
SPORT_META: dict[str, tuple[str, str, str]] = {
    "football": ("Football", "football", "football"),
    "hockey": ("Hockey", "hockey", "hockey"),
    "basketball": ("Basketball", "basketball", "basketball"),
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
            self.session.add(team)
        return team

    def backfill_icons(
        self, sport_key: str, league_key: str, icons: dict[str, str]
    ) -> None:
        """Update team icons from ALL API games regardless of match date."""
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, sport.id)
        for name, icon in icons.items():
            team = self.session.exec(
                select(Team).where(Team.name == name, Team.league_id == league.id)
            ).first()
            if team and team.icon != icon:
                team.icon = icon
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
            select(Team).where(Team.league_id.in_(league_ids))
        ).all()
        for team in teams:
            icon = icons.get(team.name)
            if icon and team.icon != icon:
                team.icon = icon
                self.session.add(team)
        self.session.commit()

    def save(self, sport_key: str, league_key: str, events: dict) -> None:
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, sport.id)

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
                event["homeTeam"], league.id, event.get("homeIcon")
            )
            away_team = self._get_or_create_team(
                event["awayTeam"], league.id, event.get("awayIcon")
            )

            home_score = _to_int(event.get("homeScore"))
            away_score = _to_int(event.get("awayScore"))

            # Each match stored twice — once per team — so calendar queries stay simple
            for team, ext_suffix in [(home_team, "home"), (away_team, "away")]:
                external_id = f"{event_id}_{ext_suffix}"
                expected_external_ids.add(external_id)
                existing = self.session.exec(
                    select(Match).where(Match.external_id == external_id)
                ).first()
                if existing:
                    existing.team_id = team.id
                    existing.home_team = event["homeTeam"]
                    existing.away_team = event["awayTeam"]
                    existing.start_time = start_time
                    existing.home_score = home_score
                    existing.away_score = away_score
                    self.session.add(existing)
                else:
                    self.session.add(
                        Match(
                            external_id=external_id,
                            team_id=team.id,
                            home_team=event["homeTeam"],
                            away_team=event["awayTeam"],
                            start_time=start_time,
                            home_score=home_score,
                            away_score=away_score,
                        )
                    )

        team_ids = [
            t.id
            for t in self.session.exec(
                select(Team).where(Team.league_id == league.id)
            ).all()
        ]
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
        "premier_league": 8,
        "uefa_champions_league": 5,
        "uefa_conference_league": 1125,
        "fa_cup": 1,
        "efl_cup": 2,
        "uefa_europa_league": 6,
    }

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _badge_url(self, team: dict) -> str | None:
        team_id = team.get("id")
        if not team_id:
            return None
        now = datetime.now()
        season_year = now.year if now.month >= 8 else now.year - 1
        yr = str(season_year)[-2:]
        return f"https://resources.premierleague.com/premierleague{yr}/badges-alt/50/{team_id}.png"

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
                    start = self.time.convert_to_utc(
                        match["kickoff"], match["kickoffTimezone"]
                    )
                    if not self.time.is_recent_or_future(start):
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

    def filter(self):
        season = self.time.get_active_season_year("09")
        for sport_key, leagues in self.LEAGUES.items():
            for league_key, league_data in leagues.items():
                events: dict = {}
                url_slug = league_data["url_slug"]
                meta = self.api.get(
                    f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter"
                )
                season_uuid, series_uuid, game_type_uuid = (
                    self.helpers.get_active_season_uuid(meta)
                )

                all_icons: dict[str, str] = {}
                for game_type in [item["uuid"] for item in game_type_uuid]:
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

                        if not self.time.is_recent_or_future(match["rawStartDateTime"]):
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
                        }
                if all_icons:
                    self.store.backfill_icons(sport_key, league_key, all_icons)
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
                    home = match.select_one(
                        ".match-list__home .match-list__team-name"
                    ).text.strip()
                    away = match.select_one(
                        ".match-list__away .match-list__team-name"
                    ).text.strip()
                    home_img = match.select_one(".match-list__home .team-logo__img")
                    away_img = match.select_one(".match-list__away .team-logo__img")
                    home_icon = home_img.get("src") if home_img else None
                    away_icon = away_img.get("src") if away_img else None
                    start = self.time.convert_to_utc(
                        match.select_one("time").get("datetime")
                    )
                    href = match.select_one(".match-list__link").get("href")
                    event_id = parse_qs(urlparse(href).query).get("fmid", [None])[0]
                    if not self.time.is_recent_or_future(start) or not event_id:
                        continue
                    events[str(event_id)] = {
                        "eventId":          str(event_id),
                        "homeTeam":         home,
                        "awayTeam":         away,
                        "startDateAndTime": start,
                        "homeIcon":         home_icon,
                        "awayIcon":         away_icon,
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
        # Badge directory year matches the PL season start year (e.g. "25" for 2025/26).
        now = datetime.now()
        season_year = now.year if now.month >= 8 else now.year - 1
        yr = str(season_year)[-2:]
        return f"https://resources.premierleague.com/premierleague{yr}/badges-alt/{code}.svg"

    def filter(self):
        data = self.api.get(self.FPL_URL)
        icons: dict[str, str] = {}
        for team in data.get("teams", []):
            code = team.get("code")
            fpl_name = team.get("name", "")
            if not code or not fpl_name:
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
        resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": ALERT_EMAIL,
                "subject": "MatchSync fetcher error",
                "text": f"MatchSync fetcher failed at {datetime.now(_LOCAL_TZ).isoformat()}\n\nError:\n{error}",
            }
        )
        print("[fetcher] error alert email sent")
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
            FootballIconsFetcher(api, store).filter()

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
