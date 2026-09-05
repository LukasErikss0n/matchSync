from datetime import datetime

import requests

from tasks.common import ExpectedUpstreamGap
from tasks.db_store import DBStore
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement


class F1Filter:
    """home_team=Grand Prix, away_team=session (Practice/Qualifying/Race)."""

    BASE_URL = "https://api.openf1.org/v1"
    LEAGUES = {"f1": None}
    LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg"

    def __init__(self, api: FetchAPI, time: TimeManagement, store: DBStore):
        self.api = api
        self.time = time
        self.store = store

    def _get_list(self, url: str) -> list:
        try:
            data = self.api.get(url)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 404:
                return []
            if status == 401:
                raise ExpectedUpstreamGap(
                    f"OpenF1 gated (401, live session in progress): {url}"
                ) from e
            raise
        return data if isinstance(data, list) else []

    def filter(self, full_history: bool = False):
        year = datetime.now().year
        events: dict = {}
        meetings = self._get_list(f"{self.BASE_URL}/meetings?year={year}")
        for meeting in meetings:
            name = meeting.get("meeting_name")
            meeting_key = meeting.get("meeting_key")
            if (
                not name
                or meeting_key is None
                or "testing" in name.lower()
                or meeting.get("is_cancelled")
            ):
                continue
            circuit = meeting.get("circuit_short_name") or meeting.get("location")
            country = meeting.get("country_name")
            venue = f"{circuit}, {country}" if circuit and country else circuit
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
                    "venue": venue,
                    "homeIcon": meeting.get("country_flag"),
                    "extraTeam": "Formula 1",
                    "extraIcon": self.LOGO_URL,
                }
        self.store.save("motorsport", "f1", events)
