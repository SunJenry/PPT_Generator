# PPT Generator

A single-command PPT generator: JSON in, `.pptx` out. Given a topic, brief, and target audience, it produces a cohesive 25–30 slide presentation with a clear narrative arc.

## Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Configuration

Set the following environment variables (or create a `.env` file):

| Variable | Required | Description |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | Yes | DeepSeek API key for the LLM |
| `UNSPLASH_ACCESS_KEY` | No | Unsplash access key for image search (skips images if unset) |

Optional overrides: `DEEPSEEK_BASE_URL` (default: `https://api.deepseek.com`), `DEEPSEEK_MODEL` (default: `deepseek-v4-flash`).

## Usage

```bash
python -m PPT_Generator input.json output.pptx
```

Input format:

```json
{
  "topic": "主题",
  "brief": "简介（≤500 字）",
  "audience": "目标受众"
}
```

See `examples/sample_input.json` for a complete example.

## How It Works

The pipeline has four stages:

1. **Planner** (LLM) — generates a narrative outline (sections + narrative arc) from `(topic, brief, audience)`
2. **Content Generator** (LLM + built-in web search) — fills the outline with per-slide structured content; the model automatically invokes DeepSeek's built-in `web_search` tool to verify factual claims (deadlines, tuition, fees, policies), cites source URLs in `source_notes`, and explicitly marks unpublished information as "Not yet published"
3. **Validator** (LLM) — checks page count (25–30), narrative coherence, and layout fit
4. **Renderer** (`python-pptx`) — renders the structured content to a `.pptx` file, optionally fetching images from Unsplash

Every LLM/image call is tracked by a cost tracker; a report with estimated cost and elapsed time is printed at the end.

## Development

```bash
# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_pipeline.py

# Run a single test function
python -m pytest tests/test_pipeline.py::test_pipeline_runs_end_to_end
```
