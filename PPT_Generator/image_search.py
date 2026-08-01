from typing import Optional

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


def _is_transient_error(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return 500 <= exception.response.status_code < 600
    return isinstance(exception, (httpx.NetworkError, httpx.TimeoutException))


class ImageSearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.access_key = settings.unsplash_access_key
        self.cost_tracker = cost_tracker

    def search(self, keyword: str) -> Optional[str]:
        if not self.access_key:
            return None
        return self._do_search(keyword)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_transient_error),
        reraise=True,
    )
    def _do_search(self, keyword: str) -> Optional[str]:
        url = "https://api.unsplash.com/search/photos"
        params = {"query": keyword, "per_page": 1, "client_id": self.access_key}
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data["results"]:
                self.cost_tracker.add_image_call()
                return data["results"][0]["urls"]["regular"]
            return None
