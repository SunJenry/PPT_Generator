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
| `ARK_API_KEY` | Yes | 火山方舟 (Volcengine Ark) API key for the LLM |
| `TAVILY_API_KEY` | Yes | Tavily API key for fact-checking search |
| `UNSPLASH_ACCESS_KEY` | No | Unsplash access key for image search (skips images if unset) |

Optional overrides: `ARK_BASE_URL` (default: `https://ark.cn-beijing.volces.com/api/v3`), `ARK_MODEL` (default: `kimi-k2.6`).

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

The pipeline has five stages:

1. **Planner** (LLM) — generates a narrative outline and a list of fact queries
2. **Researcher** (Tavily) — parallel web search to verify specific facts (deadlines, tuition, visa fees, etc.)
3. **Content Generator** (LLM) — fills the outline with per-slide structured content using constrained layouts
4. **Validator** (LLM) — checks page count, coherence, and layout fit
5. **Renderer** (`python-pptx`) — renders the structured content to a `.pptx` file, optionally fetching images from Unsplash

Every LLM/search/image call is tracked by a cost tracker; a report with estimated cost and elapsed time is printed at the end.

## Development

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_pipeline.py

# Run a single test function
pytest tests/test_pipeline.py::test_pipeline_runs_end_to_end
```
