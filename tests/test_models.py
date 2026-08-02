from PPT_Generator.models import Outline, Presentation, SectionPlan, Slide


def test_outline_requires_sections():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=5, key_points=["a"])],
    )
    assert outline.sections[0].section_title == "Intro"


def test_presentation_serialization():
    slide = Slide(page_number=1, layout_id="title", title="Test")
    pres = Presentation(
        topic="topic", audience="audience", narrative_arc="arc", slides=[slide], total_pages=1, sources=[]
    )
    data = pres.model_dump()
    assert data["total_pages"] == 1
    assert data["slides"][0]["layout_id"] == "title"
