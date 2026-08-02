import json
import os
from unittest.mock import MagicMock, patch

from PPT_Generator.models import Outline, Presentation, SectionPlan, Slide


@patch("PPT_Generator.pipeline.LLMClient")
@patch("PPT_Generator.pipeline.ImageSearchClient")
def test_full_pipeline_creates_pptx(mock_image, mock_llm, tmp_path):
    llm_instance = MagicMock()
    llm_instance.chat.side_effect = [
        Outline(
            narrative_arc="arc",
            sections=[SectionPlan(section_title="Intro", pages=25, key_points=["a"])],
        ),
        Presentation(
            topic="T", audience="A", narrative_arc="arc",
            slides=[Slide(page_number=i, layout_id="title" if i == 1 else "bullet_focus", title=f"Slide {i}") for i in range(1, 26)],
            total_pages=25, sources=["https://example.com"],
        ),
        Presentation(
            topic="T", audience="A", narrative_arc="arc",
            slides=[Slide(page_number=i, layout_id="title" if i == 1 else "bullet_focus", title=f"Slide {i}") for i in range(1, 26)],
            total_pages=25, sources=["https://example.com"],
        ),
    ]
    mock_llm.return_value = llm_instance

    input_path = tmp_path / "in.json"
    input_path.write_text(json.dumps({"topic": "T", "brief": "B", "audience": "A"}))
    output_path = tmp_path / "out.pptx"

    from PPT_Generator.cli import main

    argv = [str(input_path), str(output_path)]
    main(argv)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
