import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


def _is_transient_error(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return 500 <= exception.response.status_code < 600
    return isinstance(exception, (httpx.NetworkError, httpx.TimeoutException))


class SearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.api_key = settings.tavily_api_key
        self.cost_tracker = cost_tracker

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_transient_error),
        reraise=True,
    )
    def search(self, query: str, search_depth: str = "basic", max_results: int = 3) -> dict:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            self.cost_tracker.add_search_call()
            return response.json()
