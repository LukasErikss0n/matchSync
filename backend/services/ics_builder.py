import uuid
from datetime import timedelta
from icalendar import Alarm, Calendar, Event
from models.models import Match


def build_ics(team_name: str, matches: list[Match]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//MatchSync//matchsync.io//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"{team_name} — MatchSync")
    cal.add("refresh-interval", "PT1H")
    cal.add("x-published-ttl", "PT1H")

    for match in matches:
        event = Event()
        event.add("uid", str(uuid.uuid4()))
        event.add("summary", f"{match.home_team} vs {match.away_team}")
        event.add("dtstart", match.start_time)
        event.add("dtend", match.end_time or match.start_time + timedelta(hours=2))
        if match.venue:
            event.add("location", match.venue)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"{match.home_team} vs {match.away_team} starts in 1 hour")
        alarm.add("trigger", timedelta(hours=-1))
        event.add_component(alarm)

        cal.add_component(event)

    return cal.to_ical()
