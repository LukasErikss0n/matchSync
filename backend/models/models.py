from typing import Optional
from sqlmodel import Field, Relationship
from schemas.schemas import (
    CalendarSubscriptionBase,
    SportBase,
    LeagueBase,
    TeamBase,
    MatchBase,
)


class Sport(SportBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    leagues: list["League"] = Relationship(back_populates="sport")


class League(LeagueBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sport_id: int = Field(foreign_key="sport.id")
    sport: Optional[Sport] = Relationship(back_populates="leagues")
    teams: list["Team"] = Relationship(back_populates="league")


class Team(TeamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    league_id: int = Field(foreign_key="league.id")
    league: Optional[League] = Relationship(back_populates="teams")
    matches: list["Match"] = Relationship(back_populates="team")


class Match(MatchBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # external_id is unique per (event, team) — store once for home, once for away
    external_id: str = Field(unique=True)
    team_id: int = Field(foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="matches")


class CalendarSubscription(CalendarSubscriptionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Looked up on every feed fetch, so it carries an index, and uniqueness
    # is what makes "one row per issued link" hold.
    token: str = Field(unique=True, index=True)
