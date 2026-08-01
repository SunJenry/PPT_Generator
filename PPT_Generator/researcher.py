from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from PPT_Generator.models import FactQuery, Outline, ResearchResult
from PPT_Generator.search_client import SearchClient


class Researcher:
    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    def _search_one(self, query: FactQuery, attribute: str) -> ResearchResult:
        full_query = f"{query.entity} {attribute}"
        try:
            response = self.search_client.search(full_query)
            answer = response.get("answer", "")
            results = response.get("results", [])
            source_url = results[0].get("url", "") if results else ""
            confidence = "medium" if answer else "low"
            return ResearchResult(
                entity=query.entity,
                attribute=attribute,
                value=answer or "Not found",
                source_url=source_url,
                confidence=confidence,
            )
        except Exception:
            return ResearchResult(
                entity=query.entity,
                attribute=attribute,
                value="Search failed",
                source_url="",
                confidence="low",
            )

    def research(self, outline: Outline) -> List[ResearchResult]:
        tasks = []
        for query in outline.fact_queries:
            for attribute in query.attributes:
                tasks.append((query, attribute))
        results: List[ResearchResult] = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._search_one, q, a): (q, a) for q, a in tasks}
            for future in as_completed(futures):
                results.append(future.result())
        return results
