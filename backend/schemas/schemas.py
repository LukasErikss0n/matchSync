from datetime import datetime
from typing import Optional
from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, SQLModel


# Canonical match states (MatchBase.status). Defined here rather than in
# tasks/fetcher.py so the services/ consumers can share them without importing
# the fetcher (which imports services itself).
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
    icon: Optional[str] = None   # team logo URL — nullable (not every source provides one)
    # Primary crest colour as #rrggbb, extracted from `icon` server-side (see
    # services/crest_color.py). Nullable: no icon, or nothing legible in it.
    color: Optional[str] = None
    # `icon` cropped to its actual artwork, stored as PNG bytes and served by
    # GET /api/teams/{id}/crest.png — many source PNGs ship with a large
    # transparent margin baked in (see crest_color.py). Kept out of JSON
    # responses deliberately: inlining these as data URIs put ~700KB of base64
    # into a single match list. Nullable: no icon, source is SVG (which scales
    # losslessly already), or already tight enough to skip.
    icon_data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))


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
    # "scheduled" | "live" | "finished", normalised from whatever each source
    # calls it (see tasks/fetcher.py's _STATUS_*). None where the source gives
    # us nothing to go on — consumers fall back to a kickoff-time heuristic.
    # A score alone can't stand in for this: every provider starts reporting
    # 0-0 the moment a match kicks off, so "has a score" means "under way or
    # over", never specifically "over".
    status: Optional[str] = None
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
    home_color: Optional[str] = None
    away_color: Optional[str] = None
    # URLs to the trimmed crest (see TeamBase.icon_data), not the image data —
    # a match list carries dozens of these and inlining them was ~700KB.
    home_icon_cropped: Optional[str] = None
    away_icon_cropped: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    start_time: datetime
    venue: Optional[str] = None
    status: Optional[str] = None   # see MatchBase.status


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
