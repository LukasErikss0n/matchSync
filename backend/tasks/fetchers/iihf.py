from datetime import datetime, timezone

from tasks.db_store import DBStore
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement


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
