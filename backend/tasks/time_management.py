from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil.parser import parse


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
            return True
        return dt <= datetime.now(timezone.utc)

    RESULTS_WINDOW_DAYS = 10

    def is_recent_or_future(self, date_utc: str) -> bool:
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
