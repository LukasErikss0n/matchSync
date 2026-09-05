from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

from schemas.schemas import STATUS_FINISHED
from tasks.db_store import DBStore
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement


def _attr_str(tag: Tag | None, name: str) -> str | None:
    if tag is None:
        return None
    val = tag.get(name)
    return val if isinstance(val, str) else None


class SwedishFootballFilter:
    BASE_URL = "https://www.svenskfotboll.se"
    LEAGUES = {"allsvenskan": 133348}
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
            self._collect(
                events,
                f"/api/played-games/?competitionId={competition_id}&from=0",
                stop_when_old=True,
                status=STATUS_FINISHED,
            )
            self.store.save("football", league_key, events)

    def _collect(
        self,
        events: dict,
        start_url: str,
        stop_when_old: bool = False,
        full_history: bool = False,
        status: str | None = None,
    ) -> None:
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
                if status:
                    event["status"] = status
                venue_el = match.select_one(".match-list__location")
                if venue_el is not None and venue_el.text.strip():
                    event["venue"] = venue_el.text.strip()
                home_score_el = match.select_one(".match-list__home .match-list__score")
                away_score_el = match.select_one(".match-list__away .match-list__score")
                if home_score_el is not None:
                    event["homeScore"] = home_score_el.text.strip()
                if away_score_el is not None:
                    event["awayScore"] = away_score_el.text.strip()
            next_url = None if hit_old else page.get("nextUrl")
