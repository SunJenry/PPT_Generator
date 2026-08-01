from unittest.mock import MagicMock, patch

from PPT_Generator.models import Outline, Presentation, SectionPlan, Slide
from PPT_Generator.pipeline import Pipeline


@patch("PPT_Generator.pipeline.LLMClient")
@patch("PPT_Generator.pipeline.SearchClient")
@patch("PPT_Generator.pipeline.ImageSearchClient")
@patch("PPT_Generator.pipeline.Renderer")
def test_pipeline_runs_end_to_end(mock_renderer, mock_image, mock_search, mock_llm, tmp_path):
    llm_instance = MagicMock()
    llm_instance.chat.side_effect = [
        Outline(narrative_arc="arc", sections=[SectionPlan(section_title="Intro", pages=1, key_points=["a"])], fact_queries=[]),
        Presentation(
            topic="T", audience="A", narrative_arc="arc",
            slides=[Slide(page_number=1, layout_id="title", title="Hello")],
            total_pages=1, sources=[],
        ),
        Presentation(
            topic="T", audience="A", narrative_arc="arc",
            slides=[Slide(page_number=1, layout_id="title", title="Hello")],
            total_pages=1, sources=[],
        ),
    ]
    mock_llm.return_value = llm_instance

    search_instance = MagicMock()
    search_instance.search.return_value = {"answer": "v", "results": [{"url": "https://example.com"}]}
    mock_search.return_value = search_instance

    output = tmp_path / "out.pptx"
    pipeline = Pipeline()
    report = pipeline.run("T", "brief", "A", str(output))
    assert report["output_path"] == str(output)
    assert report["total_pages"] == 1
