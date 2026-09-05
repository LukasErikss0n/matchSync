import time as time_module
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class FetchAPI:
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Connection": "keep-alive",
    }

    def __init__(self):
        self.session = requests.Session()
        retry = Retry(
            total=5,
            read=5,
            connect=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, url: str) -> dict:
        r = self.session.get(url, headers=self.HEADERS, timeout=(5, 30))
        r.raise_for_status()
        return r.json()


_PL_BADGE_YEAR_CACHE: dict[int, tuple[float, str]] = {}
_PL_BADGE_YEAR_CACHE_TTL_SECONDS = 3 * 60 * 60


def resolve_pl_badge_year() -> str:
    now = datetime.now()
    candidate_year = now.year if now.month >= 8 else now.year - 1

    cached = _PL_BADGE_YEAR_CACHE.get(candidate_year)
    now_monotonic = time_module.monotonic()
    if cached and now_monotonic - cached[0] < _PL_BADGE_YEAR_CACHE_TTL_SECONDS:
        return cached[1]

    candidate = str(candidate_year)[-2:]
    probe_url = f"https://resources.premierleague.com/premierleague{candidate}/badges-alt/50/1.png"
    try:
        resp = requests.head(probe_url, headers=FetchAPI.HEADERS, timeout=(3, 5))
        yr = candidate if resp.status_code == 200 else str(candidate_year - 1)[-2:]
    except requests.RequestException:
        yr = str(candidate_year - 1)[-2:]

    _PL_BADGE_YEAR_CACHE[candidate_year] = (now_monotonic, yr)
    return yr
