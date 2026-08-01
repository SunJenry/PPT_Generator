from typing import Optional

import httpx

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


class ImageSearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.access_key = settings.unsplash_access_key
        self.cost_tracker = cost_tracker

    def search(self, keyword: str) -> Optional[str]:
        if not self.access_key:
            return None
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
