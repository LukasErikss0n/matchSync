from datetime import datetime

from models.models import Match, Team
from schemas.schemas import LeagueOut, MatchOut
from services.crest_url import crest_url
from utils import ensure_utc


def build_match_out(
    match: Match,
    home_team: Team,
    away_team: Team | None,
    league: LeagueOut,
    sport_slug: str,
    *,
    start: datetime | None = None,
) -> MatchOut:
    assert match.id is not None
    return MatchOut(
        id=match.id,
        external_id=match.external_id,
        sport=sport_slug,
        league=league,
        home_team=match.home_team,
        away_team=match.away_team,
        home_slug=home_team.slug,
        away_slug=away_team.slug if away_team else None,
        home_icon=home_team.icon,
        away_icon=away_team.icon if away_team else None,
        home_icon_cropped=crest_url(home_team),
        away_icon_cropped=crest_url(away_team),
        home_score=match.home_score,
        away_score=match.away_score,
        start_time=start if start is not None else ensure_utc(match.start_time),
        venue=match.venue,
        status=match.status,
    )
