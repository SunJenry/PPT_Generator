import httpx

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


class SearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.api_key = settings.tavily_api_key
        self.cost_tracker = cost_tracker

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
