from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, col, select

from models.models import League, Match, Sport, Team
from services.crest_crop import crop_crest
from tasks.common import LEAGUE_DISPLAY, SPORT_META, slugify

_PLACEHOLDER_FRAGMENTS = {
    "winner",
    "loser",
    "runner-up",
    "runner up",
    "tbd",
    "tbc",
    "semi-final",
    "semifinal",
    "quarter-final",
    "quarterfinal",
    "to be confirmed",
    "to be decided",
}


def _to_int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _is_placeholder(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in _PLACEHOLDER_FRAGMENTS)


def _pk(row: Sport | League | Team) -> int:
    assert row.id is not None
    return row.id


class DBStore:
    def __init__(self, session: Session):
        self.session = session

    def _get_or_create_sport(self, sport_key: str) -> Sport:
        name, slug, icon = SPORT_META[sport_key]
        sport = self.session.exec(select(Sport).where(Sport.slug == slug)).first()
        if not sport:
            sport = Sport(name=name, slug=slug, icon=icon)
            self.session.add(sport)
            self.session.flush()
        elif sport.icon != icon:
            sport.icon = icon
            self.session.add(sport)
        return sport

    def _get_or_create_league(self, league_key: str, sport_id: int) -> League:
        name = LEAGUE_DISPLAY.get(league_key, league_key.replace("_", " ").title())
        slug = slugify(name)
        league = self.session.exec(select(League).where(League.slug == slug)).first()
        if not league:
            league = League(name=name, slug=slug, sport_id=sport_id)
            self.session.add(league)
            self.session.flush()
        return league

    def _get_or_create_team(
        self, name: str, league_id: int, icon: str | None = None
    ) -> Team:
        team = self.session.exec(
            select(Team).where(Team.name == name, Team.league_id == league_id)
        ).first()
        if not team:
            team = Team(name=name, slug=slugify(name), league_id=league_id, icon=icon)
            self.session.add(team)
            self.session.flush()
        elif icon and team.icon != icon:
            team.icon = icon
            team.icon_data = None
            team.crest_checked = False
            self.session.add(team)
        return team

    def backfill_icons(
        self, sport_key: str, league_key: str, icons: dict[str, str]
    ) -> None:
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, _pk(sport))
        for name, icon in icons.items():
            team = self.session.exec(
                select(Team).where(Team.name == name, Team.league_id == league.id)
            ).first()
            if team and team.icon != icon:
                team.icon = icon
                team.icon_data = None
                team.crest_checked = False
                self.session.add(team)
        self.session.commit()

    def backfill_sport_icons(self, sport_slug: str, icons: dict[str, str]) -> None:
        sport = self.session.exec(select(Sport).where(Sport.slug == sport_slug)).first()
        if not sport:
            return
        league_ids = [
            l.id for l in self.session.exec(
                select(League).where(League.sport_id == sport.id)
            ).all()
        ]
        if not league_ids:
            return
        teams = self.session.exec(
            select(Team).where(col(Team.league_id).in_(league_ids))
        ).all()
        for team in teams:
            icon = icons.get(team.name)
            if icon and team.icon != icon:
                team.icon = icon
                team.icon_data = None
                team.crest_checked = False
                self.session.add(team)
        self.session.commit()

    def backfill_cropped_crests(self) -> None:
        teams = self.session.exec(
            select(Team).where(col(Team.icon).is_not(None), col(Team.crest_checked).is_(False))
        ).all()
        if not teams:
            return
        cropped_count = 0
        for team in teams:
            if not team.icon:
                continue
            cropped = crop_crest(team.icon)
            team.icon_data = cropped
            team.crest_checked = True
            self.session.add(team)
            if cropped:
                cropped_count += 1
        self.session.commit()
        print(f"[crest-crop] cropped {cropped_count}/{len(teams)} team crests")

    def save(self, sport_key: str, league_key: str, events: dict) -> None:
        sport = self._get_or_create_sport(sport_key)
        league = self._get_or_create_league(league_key, _pk(sport))

        expected_external_ids: set[str] = set()

        for event_id, event in events.items():
            if _is_placeholder(event["homeTeam"]) or _is_placeholder(event["awayTeam"]):
                continue
            try:
                start_time = datetime.fromisoformat(
                    event["startDateAndTime"].replace("Z", "+00:00")
                )
            except ValueError:
                continue
            home_team = self._get_or_create_team(
                event["homeTeam"], _pk(league), event.get("homeIcon")
            )
            away_team = self._get_or_create_team(
                event["awayTeam"], _pk(league), event.get("awayIcon")
            )

            home_score = _to_int(event.get("homeScore"))
            away_score = _to_int(event.get("awayScore"))
            venue = event.get("venue") or None
            status = event.get("status") or None
            is_playoff = bool(event.get("isPlayoff", False))
            overtime = bool(event.get("overtime", False))
            shootout = bool(event.get("shootout", False))

            perspectives = [(home_team, "home"), (away_team, "away")]
            extra_name = event.get("extraTeam")
            if extra_name:
                extra_team = self._get_or_create_team(extra_name, _pk(league), event.get("extraIcon"))
                perspectives.append((extra_team, "extra"))

            for team, ext_suffix in perspectives:
                external_id = f"{event_id}_{ext_suffix}"
                expected_external_ids.add(external_id)
                existing = self.session.exec(
                    select(Match).where(Match.external_id == external_id)
                ).first()
                if existing:
                    existing.team_id = _pk(team)
                    existing.home_team = event["homeTeam"]
                    existing.away_team = event["awayTeam"]
                    existing.start_time = start_time
                    existing.home_score = home_score
                    existing.away_score = away_score
                    if venue:
                        existing.venue = venue
                    if status:
                        existing.status = status
                    existing.is_playoff = is_playoff
                    existing.overtime = overtime
                    existing.shootout = shootout
                    self.session.add(existing)
                else:
                    self.session.add(
                        Match(
                            external_id=external_id,
                            team_id=_pk(team),
                            home_team=event["homeTeam"],
                            away_team=event["awayTeam"],
                            start_time=start_time,
                            home_score=home_score,
                            away_score=away_score,
                            venue=venue,
                            status=status,
                            is_playoff=is_playoff,
                            overtime=overtime,
                            shootout=shootout,
                        )
                    )

        team_ids = [
            _pk(t)
            for t in self.session.exec(
                select(Team).where(Team.league_id == league.id)
            ).all()
        ]
        deleted = 0
        if team_ids:
            now = datetime.now(timezone.utc)
            future_matches = self.session.exec(
                select(Match).where(
                    col(Match.team_id).in_(team_ids),
                    Match.start_time > now,
                )
            ).all()
            for m in future_matches:
                if m.external_id not in expected_external_ids:
                    self.session.delete(m)
                    deleted += 1

        self.session.commit()
        print(f"Saved {league_key} → {len(events)} events (removed {deleted} stale)")
