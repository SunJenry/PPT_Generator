from PPT_Generator.content_generator import ContentGenerator
from PPT_Generator.models import Outline, Presentation, ResearchResult, SectionPlan, Slide
from PPT_Generator.templates.registry import TemplateRegistry


class FakeLLMClient:
    def chat(self, system, user, response_format):
        return Presentation(
            topic="T",
            audience="A",
            narrative_arc="arc",
            slides=[Slide(page_number=1, layout_id="title", title="Hello")],
            total_pages=1,
            sources=["https://example.com"],
        )


def test_content_generator_returns_presentation():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=1, key_points=["a"])],
        fact_queries=[],
    )
    research = [ResearchResult(entity="E", attribute="a", value="v", source_url="https://example.com", confidence="high")]
    layouts = TemplateRegistry()
    generator = ContentGenerator(FakeLLMClient())
    pres = generator.generate("T", "A", outline, research, layouts)
    assert pres.slides[0].title == "Hello"
