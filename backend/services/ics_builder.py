from datetime import timedelta

from icalendar import Alarm, Calendar, Event, vDuration
from models.models import Match
from utils import ensure_utc

LEAGUE_SHORT_NAMES: dict[str, str] = {
    "Premier League": "Prem",
    "UEFA Champions League": "UCL",
    "UEFA Europa League": "UEL",
    "UEFA Conference League": "UECL",
    "IIHF World Championship": "IIHF WC",
    "FIFA World Cup 2026": "World Cup",
}

_NON_MATCH_LEAGUES = {"Formula 1"}


def _title(league: str | None, home_team: str, away_team: str) -> str:
    if league in _NON_MATCH_LEAGUES:
        return f"{home_team} – {away_team}"
    return f"{home_team} vs {away_team}"


def build_ics(
    team_name: str,
    matches: list[Match],
    league_by_team: dict[int, str] | None = None,
) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//Matchcalender//matchcalender.com//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"{team_name} — MatchCalender")
    cal.add("x-wr-timezone", "UTC")
    cal.add("refresh-interval", vDuration(timedelta(hours=1)))
    cal.add("x-published-ttl", vDuration(timedelta(hours=1)))

    for match in matches:
        start = ensure_utc(match.start_time)
        end = ensure_utc(match.end_time) if match.end_time else start + timedelta(hours=2)

        league = (league_by_team or {}).get(match.team_id)
        prefix = f"{LEAGUE_SHORT_NAMES.get(league, league)}: " if league else ""

        event = Event()
        event.add("uid", f"{match.external_id}@matchcalender.com")
        title = _title(league, match.home_team, match.away_team)
        event.add("summary", f"{prefix}{title}")
        event.add("dtstart", start)
        event.add("dtend", end)
        if match.venue:
            event.add("location", match.venue)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"{title} starts in 1 hour")
        alarm.add("trigger", timedelta(hours=-1))
        event.add_component(alarm)

        cal.add_component(event)

    return cal.to_ical()
