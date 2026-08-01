from PPT_Generator.models import Presentation, Slide
from PPT_Generator.templates.registry import TemplateRegistry
from PPT_Generator.validator import Validator


class FakeLLMClient:
    def chat(self, system, user, response_format):
        return Presentation(
            topic="T",
            audience="A",
            narrative_arc="arc",
            slides=[Slide(page_number=i, layout_id="bullet_focus", title=f"Slide {i}") for i in range(1, 26)],
            total_pages=25,
            sources=[],
        )


def test_validator_fixes_invalid_layout():
    validator = Validator(FakeLLMClient())
    layouts = TemplateRegistry()
    pres = Presentation(
        topic="T",
        audience="A",
        narrative_arc="arc",
        slides=[Slide(page_number=1, layout_id="nonexistent", title="T")],
        total_pages=1,
        sources=[],
    )
    result = validator.validate(pres, layouts)
    assert result.slides[0].layout_id == "bullet_focus"
