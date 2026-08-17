"""Public URL for a team's trimmed crest.

Shared by every service that builds a MatchOut so the path lives in one place
next to the route that serves it (routers/teams.py).
"""

from models.models import Team


def crest_url(team: Team | None) -> str | None:
    """URL of `team`'s trimmed crest, or None if it hasn't got one."""
    if team is None or team.id is None or not team.icon_data:
        return None
    return f"/api/teams/{team.id}/crest.png"
