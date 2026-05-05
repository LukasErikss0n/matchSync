from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


# ── Sport ─────────────────────────────────────────────────────────────────────

class SportBase(SQLModel):
    name: str
    slug: str
    icon: str


class SportCreate(SportBase):
    pass


class SportPublic(SportBase):
    id: int


# ── League ────────────────────────────────────────────────────────────────────

class LeagueBase(SQLModel):
    name: str
    slug: str
    sport_id: int


class LeagueCreate(LeagueBase):
    pass


class LeaguePublic(LeagueBase):
    id: int


# ── Team ──────────────────────────────────────────────────────────────────────

class TeamBase(SQLModel):
    name: str
    slug: str
    league_id: int


class TeamCreate(TeamBase):
    pass


class TeamPublic(TeamBase):
    id: int


# ── Match ─────────────────────────────────────────────────────────────────────

class MatchBase(SQLModel):
    external_id: str   # source system event ID — used for upserts
    home_team: str
    away_team: str
    start_time: datetime
    end_time: Optional[datetime] = None
    venue: Optional[str] = None
    team_id: int


class MatchCreate(MatchBase):
    pass


class MatchPublic(MatchBase):
    id: int


# ── Complex API response shapes ───────────────────────────────────────────────

class LeagueOut(SQLModel):
    """League info exposed to frontend."""
    name: str
    slug: str


class SportOut(SQLModel):
    """Shape the frontend expects from GET /sports."""
    id: str          # slug, e.g. "football"
    label: str       # display name, e.g. "Football"
    icon: str
    leagues: list[LeagueOut]


class TeamOut(SQLModel):
    """A team in the context of a sport, with all leagues it competes in."""
    name: str
    slug: str
    sport: str       # sport slug
    leagues: list[LeagueOut]


class CalendarLink(SQLModel):
    """Shape the frontend expects from GET /calendar."""
    team: str
    sport: str
    leagues: list[LeagueOut]
    url: str
