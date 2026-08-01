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
# Run the package
python -m PPT_Generator

# Run all tests
pytest

# Run a specific test file
pytest tests/test_PPT_Generator.py

# Run a specific test function
pytest tests/test_PPT_Generator.py::test_function_name

# Install additional dev requirements
pip install -r dev-requirements.txt
```

## Architecture Notes

The project is currently at the scaffolding stage. The package `PPT_Generator/` contains only placeholder entry points (`__init__.py`, `__main__.py`). The intended architecture, based on the assessment requirements, should separate concerns into at least:

1. **Content pipeline**: Research and planning given `(topic, brief, audience)` → structured outline with factual verification.
2. **Template system**: Slide layouts and visual design system ensuring consistency across 25–30 slides.
3. **Rendering engine**: Map structured content + templates → `.pptx` (e.g., via `python-pptx`).
4. **CLI**: Single-command interface accepting JSON input and writing `.pptx` output.

External services (LLMs, image generation, search APIs) may be used. Any service usage must be tracked for cost verification during evaluation. Stability and retry logic are required because failures count toward both time and cost.

## Reference Materials

- `招聘考题-PPT生成器.md`: Full assessment specification, including 5 public development topics, detailed scoring rubrics, and submission requirements.
- `pyproject.toml`: Package metadata and build configuration.
- `dev-requirements.txt`: Development-only dependencies (pytest, setuptools, wheel).
