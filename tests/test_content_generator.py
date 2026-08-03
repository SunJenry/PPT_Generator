from PPT_Generator.content_generator import ContentGenerator
from PPT_Generator.models import Outline, Presentation, SectionPlan, Slide
from PPT_Generator.templates.registry import TemplateRegistry


class FakeLLMClient:
    def __init__(self):
        self.use_search_calls = []

    def chat(self, system, user, response_format, use_search=False):
        self.use_search_calls.append(use_search)
        return Presentation(
            topic="T",
            audience="A",
            narrative_arc="arc",
            slides=[Slide(page_number=1, layout_id="title_slide", title="Hello")],
            total_pages=1,
            sources=["https://example.com"],
        )


def test_content_generator_returns_presentation():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=1, key_points=["a"])],
    )
    layouts = TemplateRegistry()
    generator = ContentGenerator(FakeLLMClient())
    pres = generator.generate("T", "A", outline, layouts)
    assert pres.slides[0].title == "Hello"


def test_content_generator_uses_web_search():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=1, key_points=["a"])],
    )
    layouts = TemplateRegistry()
    llm_client = FakeLLMClient()
    generator = ContentGenerator(llm_client)
    generator.generate("T", "A", outline, layouts)
    assert llm_client.use_search_calls == [True]
