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
            Slide(page_number=1, layout_id="title", title="Hello", subtitle="World"),
            Slide(page_number=2, layout_id="bullet_focus", title="Points", bullets=["a", "b"]),
        ],
        total_pages=2,
        sources=[],
    )
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        path = f.name
    renderer.render(pres, path)
    assert os.path.getsize(path) > 0
    os.unlink(path)
