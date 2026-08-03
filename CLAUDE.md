# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **PPT Generator** built for a recruiting assessment. The program takes a JSON input describing a topic, brief, and target audience, and produces a cohesive 25–30 slide `.pptx` deck.

The core challenge is generating a **stylistically consistent, narratively coherent** presentation—not 30 independent slides, and not padded with sentence splitting or repeated content. The output must have a clear beginning, development, and conclusion with an internal narrative arc.

Input format:
```json
{
  "topic": "主题",
  "brief": "简介（≤500 字）",
  "audience": "目标受众"
}
```

The program must run as a single command: JSON in, `.pptx` out. Demo outputs must be fully auto-generated with no post-generation manual edits per slide.

## Scoring Criteria (Design Constraints)

| Dimension | Weight | Key Constraint |
|---|---|---|
| Business understanding & content quality | 20 | Content must be factually accurate, up-to-date, and relevant to the audience. Factual errors or speculative claims without attribution disqualify. |
| Aesthetics | 30 | Must look like a professionally deliverable deck. No text overflow, element overlap, garbled fonts, or missing images. |
| Generation speed | 15 | Average time per slide ≤ 30s for full marks; ≤ 60s for partial; > 120s gets 0. |
| Generation cost | 20 | Average cost per slide ≤ ¥0.10 for full marks; ≤ ¥0.50 for partial; > ¥1.00 gets 0. |
| Technical generalization | 15 | Must generalize to unseen topics; no hard-coded demo content; stable with failure handling. |

Speed and cost are measured end-to-end from JSON ingestion to `.pptx` write, including content planning, model calls, data retrieval, image generation, retries, rendering, and export.

## Development Environment

- Python >= 3.9
- Build backend: `setuptools`
- Virtual environment: `.venv/` (already created and gitignored)

### Setup

```bash
# Activate the existing virtual environment
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Common Commands

```bash
# Generate a PPT from JSON input
python -m PPT_Generator input.json output.pptx

# Run all tests
pytest

# Run a specific test file
pytest tests/test_pipeline.py

# Run a specific test function
pytest tests/test_pipeline.py::test_pipeline_runs_end_to_end

# Install additional dev requirements
pip install -r dev-requirements.txt
```

See `examples/sample_input.json` for the input format. A sample end-to-end run (mocked external services) lives in `tests/test_integration.py`.

## Architecture

The package implements a four-stage pipeline, orchestrated by `Pipeline` (`PPT_Generator/pipeline.py`):

1. **Planner** (`planner.py`): LLM generates a narrative outline (`Outline` with sections) from `(topic, brief, audience)`.
2. **Content Generator** (`content_generator.py`): LLM fills the outline into a `Presentation` of 25–30 `Slide` objects; the call passes DeepSeek's built-in `web_search` tool so the model verifies factual claims itself and cites source URLs in `source_notes`.
3. **Validator** (`validator.py`): LLM checks page count (25–30), coherence, and layout fit; fixes invalid layout IDs locally.
4. **Renderer** (`renderer.py`): Maps structured content to template layouts via `python-pptx`, optionally fetching images from Unsplash.

Supporting modules:
- `models.py`: Pydantic contracts (`Outline`, `Slide`, `Presentation`) shared across stages. `Slide` supports 10 layout types via dedicated fields (`bullets`, `cards`, `timeline_items`, `table`, `highlight_number`, `quote_text`, etc.).
- `design.py`: Centralized design system — all colors, fonts, spacing, safe areas, and common drawing helpers (`draw_header`, `draw_footer`, `add_textbox`, etc.). The single source of truth for visual consistency.
- `templates/`: Layout system — `base.py` (abstract `BaseLayout`), `registry.py` (maps `layout_id` → layout instance), `styles.py` (backward-compat re-exports from `design.py`), `layouts/` holds 10 layout renderers: `title_slide`, `section_divider`, `content`, `two_column`, `three_card`, `timeline`, `comparison_table`, `data_highlight`, `quote`, `closing`.
- `template_builder.py`: Generates `assets/template.pptx` — a standalone reference file showcasing all 10 layouts with sample content. Users can open this in PowerPoint to preview the design. Run via `python -m PPT_Generator.template_builder`.
- `llm_client.py`: OpenAI Responses API client for DeepSeek (`deepseek-v4-flash`) with tenacity retries, optional `web_search` tool, JSON Schema injection, and markdown-fence stripping.
- `image_search.py`: Unsplash client with retries.
- `cost_tracker.py`: Accumulates LLM tokens and image call counts, estimates RMB cost using DeepSeek v4-flash pricing.
- `cli.py`: `python -m PPT_Generator input.json output.pptx`.

Configuration is environment-driven (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, optional `UNSPLASH_ACCESS_KEY`), loaded by `config.py`. Legacy Ark/Tavily settings remain in `config.py` as unused fallbacks. External call failures are logged to stderr; the pipeline degrades gracefully (validation failures continue with un-validated data).

## Reference Materials

- `招聘考题-PPT生成器.md`: Full assessment specification, including 5 public development topics, detailed scoring rubrics, and submission requirements.
- `pyproject.toml`: Package metadata and build configuration.
- `dev-requirements.txt`: Development-only dependencies (pytest, setuptools, wheel).
