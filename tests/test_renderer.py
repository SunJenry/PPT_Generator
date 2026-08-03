import os
import tempfile

from PPT_Generator.models import Presentation, Slide
from PPT_Generator.renderer import Renderer
from PPT_Generator.templates.registry import TemplateRegistry


def test_renderer_creates_pptx():
    templates = TemplateRegistry()
    renderer = Renderer(templates)
    pres = Presentation(
        topic="T",
        audience="A",
        narrative_arc="arc",
        slides=[
            Slide(page_number=1, layout_id="title_slide", title="Hello", subtitle="World"),
            Slide(page_number=2, layout_id="content", title="Points", bullets=["a", "b"]),
            Slide(page_number=3, layout_id="closing", title="Thanks", closing_text="Thank you"),
        ],
        total_pages=3,
        sources=[],
    )
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        path = f.name
    renderer.render(pres, path)
    assert os.path.getsize(path) > 0
    os.unlink(path)
