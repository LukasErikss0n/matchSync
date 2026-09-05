from models.models import Team


def crest_url(team: Team | None) -> str | None:
    if team is None or team.id is None or not team.icon_data:
        return None
    return f"/api/teams/{team.id}/crest.png"
