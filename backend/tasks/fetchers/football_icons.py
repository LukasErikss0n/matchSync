from tasks.db_store import DBStore
from tasks.http_client import FetchAPI, resolve_pl_badge_year


class FootballIconsFetcher:
    FPL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

    NAME_MAP: dict[str, str] = {
        "Man City":       "Manchester City",
        "Man Utd":        "Manchester United",
        "Spurs":          "Tottenham Hotspur",
        "Wolves":         "Wolverhampton Wanderers",
        "Newcastle":      "Newcastle United",
        "West Ham":       "West Ham United",
        "Nott'm Forest":  "Nottingham Forest",
        "Brighton":       "Brighton and Hove Albion",
        "Bournemouth":    "Bournemouth",
        "Leicester":      "Leicester City",
        "Ipswich":        "Ipswich Town",
        "Leeds":          "Leeds United",
        "Luton":          "Luton Town",
        "Sheffield Utd":  "Sheffield United",
        "Middlesbrough":  "Middlesbrough",
        "Sunderland":     "Sunderland",
    }

    def __init__(self, api: FetchAPI, store: DBStore):
        self.api = api
        self.store = store

    def _badge_url(self, code: int) -> str:
        yr = resolve_pl_badge_year()
        return f"https://resources.premierleague.com/premierleague{yr}/badges-alt/{code}.svg"

    def filter(self):
        data = self.api.get(self.FPL_URL)
        icons: dict[str, str] = {}
        for team in data.get("teams", []):
            code = team.get("code")
            fpl_name = team.get("name")
            if not isinstance(code, int) or not isinstance(fpl_name, str) or not fpl_name:
                continue
            db_name = self.NAME_MAP.get(fpl_name, fpl_name)
            icons[db_name] = self._badge_url(code)

        if icons:
            self.store.backfill_sport_icons("football", icons)
            print(f"[football-icons] updated {len(icons)} team crests")
