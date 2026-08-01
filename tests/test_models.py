from PPT_Generator.models import FactQuery, Outline, Presentation, ResearchResult, SectionPlan, Slide


def test_research_result_confidence_validation():
    valid = ResearchResult(
        entity="Imperial", attribute="tuition", value="£35k", source_url="https://example.com", confidence="high"
    )
    assert valid.confidence == "high"


def test_presentation_serialization():
    slide = Slide(page_number=1, layout_id="title", title="Test")
    pres = Presentation(
        topic="topic", audience="audience", narrative_arc="arc", slides=[slide], total_pages=1, sources=[]
    )
    data = pres.model_dump()
    assert data["total_pages"] == 1
    assert data["slides"][0]["layout_id"] == "title"
