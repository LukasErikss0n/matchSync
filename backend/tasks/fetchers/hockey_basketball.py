from schemas.schemas import STATUS_FINISHED, STATUS_LIVE, STATUS_SCHEDULED
from tasks.common import is_playoff_game_type
from tasks.db_store import DBStore
from tasks.http_client import FetchAPI
from tasks.time_management import TimeManagement


def _shl_status(state: str | None) -> str | None:
    if not state:
        return None
    if state == "pre-game":
        return STATUS_SCHEDULED
    if state == "post-game":
        return STATUS_FINISHED
    if state == "ongoing":
        return STATUS_LIVE
    return None


class HelpFunctions:
    def get_active_season_uuid(self, meta: dict):
        return (
            meta["defaultSsgtFilter"]["season"],
            meta["defaultSsgtFilter"]["series"],
            meta["gameType"],
        )


class HockeyBasketballFilter:
    LEAGUES = {
        "hockey": {
            "shl": {"url_slug": "shl"},
            "sdhl": {"url_slug": "sdhl"},
        },
        "basketball": {
            "sblherrar": {"url_slug": "sblherr"},
            "sbldamer": {"url_slug": "sbldam"},
        },
    }

    def __init__(
        self,
        api: FetchAPI,
        time: TimeManagement,
        store: DBStore,
        helpers: HelpFunctions,
    ):
        self.api = api
        self.time = time
        self.store = store
        self.helpers = helpers

    def filter(self, full_history: bool = False, league_keys: set[str] | None = None):
        season = self.time.get_active_season_year("09")
        for sport_key, leagues in self.LEAGUES.items():
            for league_key, league_data in leagues.items():
                if league_keys is not None and league_key not in league_keys:
                    continue
                events: dict = {}
                url_slug = league_data["url_slug"]
                meta = self.api.get(
                    f"https://www.{url_slug}.se/api/sports-v2/season-series-game-types-filter"
                )
                season_uuid, series_uuid, game_type_uuid = (
                    self.helpers.get_active_season_uuid(meta)
                )

                all_icons: dict[str, str] = {}
                for game_type_item in game_type_uuid:
                    game_type = game_type_item["uuid"]
                    is_playoff = is_playoff_game_type(game_type_item)
                    url = (
                        f"https://www.{url_slug}.se/api/sports-v2/game-schedule"
                        f"?seasonUuid={season_uuid}&seriesUuid={series_uuid}"
                        f"&gameTypeUuid={game_type}&gamePlace=all&played=all"
                    )
                    match_data = self.api.get(url)
                    for match in match_data["gameInfo"]:
                        if (
                            "names" not in match["homeTeamInfo"]
                            or "names" not in match["awayTeamInfo"]
                        ):
                            continue
                        for info in [match["homeTeamInfo"], match["awayTeamInfo"]]:
                            icon = info.get("icon")
                            if icon:
                                all_icons[info["names"]["full"]] = icon

                        if not full_history and not self.time.is_recent_or_future(match["rawStartDateTime"]):
                            continue
                        event_id = match["uuid"]
                        events[event_id] = {
                            "eventId": event_id,
                            "homeTeam": match["homeTeamInfo"]["names"]["full"],
                            "awayTeam": match["awayTeamInfo"]["names"]["full"],
                            "startDateAndTime": match["rawStartDateTime"],
                            "venue": (match.get("venueInfo") or {}).get("name"),
                            "status": _shl_status(match.get("state")),
                            "homeIcon": match["homeTeamInfo"].get("icon"),
                            "awayIcon": match["awayTeamInfo"].get("icon"),
                            "homeScore": match["homeTeamInfo"].get("score"),
                            "awayScore": match["awayTeamInfo"].get("score"),
                            "isPlayoff": is_playoff,
                            "overtime": bool(match.get("overtime")),
                            "shootout": bool(match.get("shootout")),
                        }
                if all_icons:
                    self.store.backfill_icons(sport_key, league_key, all_icons)
                self.store.save(sport_key, league_key, events)
