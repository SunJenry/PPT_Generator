from PPT_Generator.models import FactQuery, Outline, SectionPlan
from PPT_Generator.researcher import Researcher


class FakeSearchClient:
    def __init__(self):
        self.calls = 0

    def search(self, query):
        self.calls += 1
        return {"answer": "£35k", "results": [{"url": "https://example.com"}]}


def test_researcher_returns_results():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=5, key_points=[])],
        fact_queries=[FactQuery(entity="Imperial", attributes=["tuition", "deadline"])],
    )
    search_client = FakeSearchClient()
    researcher = Researcher(search_client)
    results = researcher.research(outline)
    assert len(results) == 2
    assert results[0].value == "£35k"
    assert search_client.calls == 2
