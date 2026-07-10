from datetime import timedelta, timezone

from icalendar import Alarm, Calendar, Event, vDuration
from models.models import Match

# Short league labels for event titles; leagues not listed use their full name.
LEAGUE_SHORT_NAMES: dict[str, str] = {
    "Premier League": "Prem",
    "UEFA Champions League": "UCL",
    "UEFA Europa League": "UEL",
    "UEFA Conference League": "UECL",
    "IIHF World Championship": "IIHF WC",
    "FIFA World Cup 2026": "World Cup",
}


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
        # Ensure start_time is UTC-aware
        start = match.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        end = match.end_time or start + timedelta(hours=2)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        league = (league_by_team or {}).get(match.team_id)
        prefix = f"{LEAGUE_SHORT_NAMES.get(league, league)}: " if league else ""

        event = Event()
        # Stable UID derived from external_id — must not change between refreshes
        event.add("uid", f"{match.external_id}@matchcalender.com")
        event.add("summary", f"{prefix}{match.home_team} vs {match.away_team}")
        event.add("dtstart", start)
        event.add("dtend", end)
        if match.venue:
            event.add("location", match.venue)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add(
            "description", f"{match.home_team} vs {match.away_team} starts in 1 hour"
        )
        alarm.add("trigger", timedelta(hours=-1))
        event.add_component(alarm)

        cal.add_component(event)

    return cal.to_ical()
