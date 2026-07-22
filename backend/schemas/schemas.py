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
    icon: Optional[str] = None   # team logo URL — nullable (not every source provides one)


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
    home_score: Optional[int] = None   # nullable — only set once a match is played
    away_score: Optional[int] = None
    team_id: int
    # Hockey/basketball only — their game-schedule feed mixes regular-season
    # and playoff games with no other way to tell them apart (see
    # tasks/fetcher.py's is_playoff_game_type). Always False elsewhere.
    is_playoff: bool = False
    # Hockey only — needed for the 3-2-1-0 points system (regulation win/
    # OT-or-shootout win/OT-or-shootout loss/regulation loss), which a plain
    # score can't tell apart from a normal win. Always False elsewhere.
    overtime: bool = False
    shootout: bool = False


class MatchCreate(MatchBase):
    pass


class MatchPublic(MatchBase):
    id: int


# ── Complex API response shapes ───────────────────────────────────────────────

class LeagueOut(SQLModel):
    """League info exposed to frontend."""
    name: str
    slug: str
    supports_standings: bool = False


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
    icon: Optional[str] = None
    leagues: list[LeagueOut]


class MatchOut(SQLModel):
    """A single fixture/result exposed to the frontend (deduplicated)."""
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
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    start_time: datetime


class SeasonStatsOut(SQLModel):
    """Live season overview for a league, computed from the same external
    providers the fetcher uses (not our own DB, which may only hold a partial
    window). `regular_season_count` excludes playoff-stage games where that
    distinction exists (currently only the Swedish hockey/basketball leagues);
    for everything else it's simply the total tracked match count."""
    published: bool         # False when the competition's fixtures aren't out yet
    season_start: Optional[datetime] = None
    regular_season_count: int
    # True for pure knockout cups (FA Cup, EFL Cup) whose later rounds are drawn
    # only once earlier ones finish — `regular_season_count` there means "matches
    # currently scheduled", not a fixed season total.
    progressive_knockout: bool = False


class StandingEntryOut(SQLModel):
    """One row of a league table, enriched with our own team slug/icon (when
    we have a matching Team row) so the frontend can reuse TeamBadge."""
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
    form: list[str] = []   # last few results, oldest → newest, each "W"/"D"/"L"


class CalendarLink(SQLModel):
    """Shape the frontend expects from GET /calendar."""
    team: str
    sport: str
    leagues: list[LeagueOut]
    url: str
