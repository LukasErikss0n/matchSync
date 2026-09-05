from datetime import datetime
from typing import Optional
from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, SQLModel


STATUS_SCHEDULED = "scheduled"
STATUS_LIVE = "live"
STATUS_FINISHED = "finished"


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
    icon: Optional[str] = None
    icon_data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    crest_checked: bool = False


class TeamCreate(TeamBase):
    pass


class TeamPublic(TeamBase):
    id: int


# ── Match ─────────────────────────────────────────────────────────────────────

class MatchBase(SQLModel):
    external_id: str
    home_team: str
    away_team: str
    start_time: datetime
    end_time: Optional[datetime] = None
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None
    team_id: int
    is_playoff: bool = False
    overtime: bool = False
    shootout: bool = False


class MatchCreate(MatchBase):
    pass


class MatchPublic(MatchBase):
    id: int


# ── Complex API response shapes ───────────────────────────────────────────────

class LeagueOut(SQLModel):
    name: str
    slug: str
    supports_standings: bool = False


class SportOut(SQLModel):
    id: str
    label: str
    icon: str
    leagues: list[LeagueOut]


class TeamOut(SQLModel):
    name: str
    slug: str
    sport: str
    icon: Optional[str] = None
    leagues: list[LeagueOut]


class MatchOut(SQLModel):
    id: int
    external_id: str
    sport: str
    league: LeagueOut
    home_team: str
    away_team: str
    home_slug: Optional[str] = None
    away_slug: Optional[str] = None
    home_icon: Optional[str] = None
    away_icon: Optional[str] = None
    home_icon_cropped: Optional[str] = None
    away_icon_cropped: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    start_time: datetime
    venue: Optional[str] = None
    status: Optional[str] = None


class SeasonStatsOut(SQLModel):
    published: bool
    season_start: Optional[datetime] = None
    regular_season_count: int
    progressive_knockout: bool = False


class StandingEntryOut(SQLModel):
    position: int
    team: str
    team_slug: Optional[str] = None
    team_icon: Optional[str] = None
    played: int
    won: int
    drawn: int
    lost: int
    goal_difference: int
    points: int
    form: list[str] = []


class CalendarLink(SQLModel):
    team: str
    sport: str
    leagues: list[LeagueOut]
    url: str


# ── Calendar subscriptions ────────────────────────────────────────────────────

class CalendarSubscriptionBase(SQLModel):
    token: str
    sport_slug: str
    team_slug: str
    team_name: str
    leagues: str
    created_at: datetime
    last_seen: Optional[datetime] = None
    fetch_count: int = 0
    last_user_agent: Optional[str] = None


class CalendarSubscriptionOut(SQLModel):
    token: str
    sport: str
    team: str
    leagues: list[str]
    created_at: datetime
    last_seen: Optional[datetime] = None
    fetch_count: int
    last_user_agent: Optional[str] = None
    active: bool


class SubscriptionDashboardOut(SQLModel):
    active_count: int
    pending_count: int
    dormant_count: int
    active_window_days: int
    subscriptions: list[CalendarSubscriptionOut]
