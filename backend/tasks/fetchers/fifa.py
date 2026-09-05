from tasks.db_store import DBStore
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement


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
        url = team.get("PictureUrl")
        if not url:
            return None
        return url.replace("{format}", "sq").replace("{size}", "4")

    def _venue(self, match: dict) -> str | None:
        stadium = match.get("Stadium") or {}
        names = stadium.get("Name") or []
        name = names[0]["Description"] if names else None
        if not name:
            return None
        cities = stadium.get("CityName") or []
        city = cities[0]["Description"] if cities else None
        return f"{name}, {city}" if city else name

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
                    "venue": self._venue(match),
                    "homeIcon": self._picture_url(home),
                    "awayIcon": self._picture_url(away),
                    "homeScore": home.get("Score"),
                    "awayScore": away.get("Score"),
                }
            self.store.save("football", tournament_key, events)
