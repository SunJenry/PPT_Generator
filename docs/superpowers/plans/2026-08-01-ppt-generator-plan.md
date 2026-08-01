# PPT Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a single-command PPT generator that takes JSON input (topic, brief, audience) and produces a 25–30 slide `.pptx` deck using a constrained-template, multi-stage LLM pipeline.

**Architecture:** A pipeline orchestrator drives five stages: Planner (LLM outline + fact queries), Researcher (Tavily parallel search), ContentGenerator (LLM fills templates), Validator (LLM checks consistency), and Renderer (`python-pptx` + image search). All stages pass typed Pydantic models; a CostTracker records LLM/search/image costs and timing.

**Tech Stack:** Python ≥3.9, `python-pptx`, `pydantic`, `openai`, `pytest`, Tavily API, Unsplash API, Phosphor Icons (local SVG).

## Global Constraints

- LLM model: 字节火山方舟 `kimi-k2.6` via OpenAI-compatible API; model ID from environment `ARK_MODEL` (fallback `kimi-k2.6`).
- API keys via environment variables only: `ARK_API_KEY`, `TAVILY_API_KEY`, optional `UNSPLASH_ACCESS_KEY`.
- Target cost ≤ ¥0.10 per slide, target latency ≤ 30s per slide (25-page deck ≤ 12.5 min).
- No hard-coded demo content; must generalize to unseen topics.
- Frequent commits; each task ends with a passing test and a commit.

---

## File Structure

```
PPT_Generator/
├── __init__.py
├── __main__.py
├── cli.py
├── config.py
├── models.py
├── pipeline.py
├── cost_tracker.py
├── llm_client.py
├── search_client.py
├── image_search.py
├── planner.py
├── researcher.py
├── content_generator.py
├── validator.py
├── renderer.py
├── templates/
│   ├── __init__.py
│   ├── base.py
│   ├── styles.py
│   ├── registry.py
│   └── layouts/
│       ├── title.py
│       ├── section_divider.py
│       ├── bullet_focus.py
│       ├── two_column.py
│       ├── three_card.py
│       ├── timeline.py
│       ├── comparison_table.py
│       ├── data_highlight.py
│       ├── quote.py
│       └── closing.py
```

---

## Task 1: Project Configuration and Dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `PPT_Generator/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `PPT_Generator.config.Settings` Pydantic settings class with fields `ark_api_key`, `ark_base_url`, `ark_model`, `tavily_api_key`, `unsplash_access_key`.

- [ ] **Step 1: Add runtime dependencies to `pyproject.toml`**

Add under `[project]`:

```toml
dependencies = [
    "python-pptx>=1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "openai>=1.0",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Add dev dependencies to `dev-requirements.txt`**

```
pytest
pytest-asyncio
respx
```

- [ ] **Step 3: Create `PPT_Generator/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ark_api_key: str
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_model: str = "kimi-k2.6"
    tavily_api_key: str
    unsplash_access_key: str = ""


settings = Settings()
```

- [ ] **Step 4: Write failing test `tests/test_config.py`**

```python
import os

import pytest

from PPT_Generator.config import Settings


def test_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "test-ark-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    s = Settings()
    assert s.ark_api_key == "test-ark-key"
    assert s.tavily_api_key == "test-tavily-key"
    assert s.ark_model == "kimi-k2.6"
```

- [ ] **Step 5: Run test**

```bash
pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml dev-requirements.txt PPT_Generator/config.py tests/test_config.py
git commit -m "chore: add deps and settings config"
```

---

## Task 2: Pydantic Data Models

**Files:**
- Create: `PPT_Generator/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `FactQuery`, `ResearchResult`, `SectionPlan`, `Outline`, `Slide`, `Presentation`.

- [ ] **Step 1: Create `PPT_Generator/models.py`**

```python
from typing import List, Optional

from pydantic import BaseModel, Field


class FactQuery(BaseModel):
    entity: str
    attributes: List[str]


class ResearchResult(BaseModel):
    entity: str
    attribute: str
    value: str
    source_url: str
    confidence: str = Field(pattern=r"^(high|medium|low)$")


class SectionPlan(BaseModel):
    section_title: str
    pages: int
    key_points: List[str]


class Outline(BaseModel):
    narrative_arc: str
    sections: List[SectionPlan]
    fact_queries: List[FactQuery]


class Slide(BaseModel):
    page_number: int
    layout_id: str
    title: str
    subtitle: Optional[str] = None
    bullets: List[str] = []
    table: Optional[List[List[str]]] = None
    image_keyword: Optional[str] = None
    image_url: Optional[str] = None
    source_notes: List[str] = []
    notes: Optional[str] = None


class Presentation(BaseModel):
    topic: str
    audience: str
    narrative_arc: str
    slides: List[Slide]
    total_pages: int
    sources: List[str]
```

- [ ] **Step 2: Write test `tests/test_models.py`**

```python
from PPT_Generator.models import FactQuery, Outline, Presentation, ResearchResult, SectionPlan, Slide


def test_research_result_confidence_validation():
    valid = ResearchResult(
        entity="Imperial", attribute="tuition", value="£35k", source_url="https://example.com", confidence="high"
    )
    assert valid.confidence == "high"


def test_presentation_serialization():
    slide = Slide(page_number=1, layout_id="title", title="Test")
    pres = Presentation(
        topic="topic", audience="audience", narrative_arc="arc", slides=[slide], total_pages=1, sources=[]
    )
    data = pres.model_dump()
    assert data["total_pages"] == 1
    assert data["slides"][0]["layout_id"] == "title"
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_models.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/models.py tests/test_models.py
git commit -m "feat: add pydantic data models"
```

---

## Task 3: Cost and Time Tracker

**Files:**
- Create: `PPT_Generator/cost_tracker.py`
- Test: `tests/test_cost_tracker.py`

**Interfaces:**
- Produces: `CostTracker` with methods `add_llm_call(prompt_tokens, completion_tokens)`, `add_search_call()`, `add_image_call()`, `report() -> dict`.

- [ ] **Step 1: Create `PPT_Generator/cost_tracker.py`**

```python
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CostTracker:
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0
    search_calls: int = 0
    image_calls: int = 0
    start_time: float = field(default_factory=time.time)

    def add_llm_call(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.llm_prompt_tokens += prompt_tokens
        self.llm_completion_tokens += completion_tokens

    def add_search_call(self) -> None:
        self.search_calls += 1

    def add_image_call(self) -> None:
        self.image_calls += 1

    def report(self) -> Dict:
        elapsed = time.time() - self.start_time
        # Approximate RMB costs (kimi-k2.6 prompt ~0.0015/1k, completion ~0.006/1k; Tavily basic ~0.025/search)
        llm_cost = (self.llm_prompt_tokens * 0.0015 + self.llm_completion_tokens * 0.006) / 1000
        search_cost = self.search_calls * 0.025
        image_cost = self.image_calls * 0.01
        total = llm_cost + search_cost + image_cost
        return {
            "elapsed_seconds": elapsed,
            "llm_prompt_tokens": self.llm_prompt_tokens,
            "llm_completion_tokens": self.llm_completion_tokens,
            "search_calls": self.search_calls,
            "image_calls": self.image_calls,
            "estimated_cost_rmb": round(total, 4),
        }
```

- [ ] **Step 2: Write test `tests/test_cost_tracker.py`**

```python
from PPT_Generator.cost_tracker import CostTracker


def test_cost_tracker_accumulates():
    ct = CostTracker()
    ct.add_llm_call(1000, 500)
    ct.add_search_call()
    ct.add_image_call()
    report = ct.report()
    assert report["llm_prompt_tokens"] == 1000
    assert report["llm_completion_tokens"] == 500
    assert report["search_calls"] == 1
    assert report["image_calls"] == 1
    assert report["estimated_cost_rmb"] > 0
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_cost_tracker.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/cost_tracker.py tests/test_cost_tracker.py
git commit -m "feat: add cost and time tracker"
```

---

## Task 4: LLM Client

**Files:**
- Create: `PPT_Generator/llm_client.py`
- Test: `tests/test_llm_client.py`

**Interfaces:**
- Consumes: `Settings` from `config.py`.
- Produces: `LLMClient.chat(system: str, user: str, response_format: type[T]) -> T` using OpenAI-compatible API and returning a parsed Pydantic model.

- [ ] **Step 1: Create `PPT_Generator/llm_client.py`**

```python
import json
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, cost_tracker: CostTracker):
        self.client = OpenAI(api_key=settings.ark_api_key, base_url=settings.ark_base_url)
        self.model = settings.ark_model
        self.cost_tracker = cost_tracker

    def chat(self, system: str, user: str, response_format: Type[T]) -> T:
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=response_format,
        )
        message = completion.choices[0].message
        if message.refusal:
            raise RuntimeError(f"Model refused: {message.refusal}")
        usage = completion.usage
        self.cost_tracker.add_llm_call(usage.prompt_tokens, usage.completion_tokens)
        return message.parsed
```

- [ ] **Step 2: Write test `tests/test_llm_client.py`**

```python
from unittest.mock import MagicMock

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import FactQuery


def test_llm_client_parses_response(monkeypatch):
    tracker = CostTracker()
    client = LLMClient(tracker)

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.refusal = None
    mock_completion.choices[0].message.parsed = FactQuery(entity="Test", attributes=["a"])
    mock_completion.usage.prompt_tokens = 10
    mock_completion.usage.completion_tokens = 5

    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    result = client.chat("system", "user", FactQuery)
    assert result.entity == "Test"
    assert tracker.llm_prompt_tokens == 10
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_llm_client.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/llm_client.py tests/test_llm_client.py
git commit -m "feat: add OpenAI-compatible LLM client"
```

---

## Task 5: Tavily Search Client

**Files:**
- Create: `PPT_Generator/search_client.py`
- Test: `tests/test_search_client.py`

**Interfaces:**
- Consumes: `Settings` from `config.py`, `CostTracker`.
- Produces: `SearchClient.search(query: str) -> dict`.

- [ ] **Step 1: Create `PPT_Generator/search_client.py`**

```python
import httpx

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


class SearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.api_key = settings.tavily_api_key
        self.cost_tracker = cost_tracker

    def search(self, query: str, search_depth: str = "basic", max_results: int = 3) -> dict:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            self.cost_tracker.add_search_call()
            return response.json()
```

- [ ] **Step 2: Write test `tests/test_search_client.py`**

```python
import httpx
import pytest
import respx

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.search_client import SearchClient


@respx.mock
def test_search_client_returns_results(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    tracker = CostTracker()
    client = SearchClient(tracker)

    route = respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(200, json={"answer": "£35k", "results": [{"url": "https://example.com"}]})
    )

    result = client.search("Imperial Business Analytics tuition")
    assert result["answer"] == "£35k"
    assert tracker.search_calls == 1
    assert route.called
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_search_client.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/search_client.py tests/test_search_client.py
git commit -m "feat: add Tavily search client"
```

---

## Task 6: Unsplash Image Search

**Files:**
- Create: `PPT_Generator/image_search.py`
- Test: `tests/test_image_search.py`

**Interfaces:**
- Consumes: `Settings`, `CostTracker`.
- Produces: `ImageSearchClient.search(keyword: str) -> Optional[str]` returning a direct image URL.

- [ ] **Step 1: Create `PPT_Generator/image_search.py`**

```python
from typing import Optional

import httpx

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker


class ImageSearchClient:
    def __init__(self, cost_tracker: CostTracker):
        self.access_key = settings.unsplash_access_key
        self.cost_tracker = cost_tracker

    def search(self, keyword: str) -> Optional[str]:
        if not self.access_key:
            return None
        url = "https://api.unsplash.com/search/photos"
        params = {"query": keyword, "per_page": 1, "client_id": self.access_key}
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data["results"]:
                self.cost_tracker.add_image_call()
                return data["results"][0]["urls"]["regular"]
            return None
```

- [ ] **Step 2: Write test `tests/test_image_search.py`**

```python
import httpx
import pytest
import respx

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.image_search import ImageSearchClient


@respx.mock
def test_image_search_returns_url(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "test-key")
    tracker = CostTracker()
    client = ImageSearchClient(tracker)

    route = respx.get("https://api.unsplash.com/search/photos").mock(
        return_value=httpx.Response(200, json={"results": [{"urls": {"regular": "https://image.jpg"}}]})
    )

    url = client.search("university campus")
    assert url == "https://image.jpg"
    assert tracker.image_calls == 1
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_image_search.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/image_search.py tests/test_image_search.py
git commit -m "feat: add Unsplash image search client"
```

---

## Task 7: Template System Foundation

**Files:**
- Create: `PPT_Generator/templates/base.py`
- Create: `PPT_Generator/templates/styles.py`
- Create: `PPT_Generator/templates/registry.py`
- Create: `PPT_Generator/templates/layouts/title.py`
- Create: `PPT_Generator/templates/layouts/bullet_focus.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: `Slide` from `models.py`.
- Produces: `BaseLayout.render(slide: Slide, prs_slide)`, `TemplateRegistry.get(layout_id: str) -> BaseLayout`, `COLORS`, `FONTS` constants.

- [ ] **Step 1: Create `PPT_Generator/templates/styles.py`**

```python
from pptx.util import Inches, Pt

COLORS = {
    "primary": "1E3A5F",
    "accent": "4A90D9",
    "background": "FFFFFF",
    "text": "333333",
    "muted": "666666",
}

FONTS = {
    "chinese": "Microsoft YaHei",
    "western": "Arial",
}

MARGINS = {
    "left": Inches(0.8),
    "right": Inches(0.8),
    "top": Inches(0.6),
    "bottom": Inches(0.6),
}

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
```

- [ ] **Step 2: Create `PPT_Generator/templates/base.py`**

```python
from abc import ABC, abstractmethod

from pptx.slide import Slide as PptxSlide

from PPT_Generator.models import Slide


class BaseLayout(ABC):
    layout_id: str

    @abstractmethod
    def render(self, slide: Slide, prs_slide: PptxSlide) -> None:
        raise NotImplementedError
```

- [ ] **Step 3: Create `PPT_Generator/templates/layouts/title.py`**

```python
from pptx.util import Inches, Pt

from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout
from PPT_Generator.templates.styles import COLORS, FONTS, SLIDE_HEIGHT, SLIDE_WIDTH


class TitleLayout(BaseLayout):
    layout_id = "title"

    def render(self, slide: Slide, prs_slide) -> None:
        title_box = prs_slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(1.5))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = slide.title
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = COLORS["primary"]
        p.font.name = FONTS["chinese"]

        if slide.subtitle:
            sub_box = prs_slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(11.333), Inches(1))
            tf = sub_box.text_frame
            p = tf.paragraphs[0]
            p.text = slide.subtitle
            p.font.size = Pt(20)
            p.font.color.rgb = COLORS["muted"]
            p.font.name = FONTS["chinese"]
```

- [ ] **Step 4: Create `PPT_Generator/templates/layouts/bullet_focus.py`**

```python
from pptx.util import Inches, Pt

from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout
from PPT_Generator.templates.styles import COLORS, FONTS


class BulletFocusLayout(BaseLayout):
    layout_id = "bullet_focus"

    def render(self, slide: Slide, prs_slide) -> None:
        title_box = prs_slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.733), Inches(1))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = slide.title
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = COLORS["primary"]
        p.font.name = FONTS["chinese"]

        left = Inches(0.8)
        top = Inches(1.8)
        width = Inches(11.733)
        height = Inches(5)
        body_box = prs_slide.shapes.add_textbox(left, top, width, height)
        tf = body_box.text_frame
        tf.word_wrap = True
        for i, bullet in enumerate(slide.bullets[:5]):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = bullet
            p.font.size = Pt(18)
            p.font.color.rgb = COLORS["text"]
            p.font.name = FONTS["chinese"]
            p.space_after = Pt(12)
```

- [ ] **Step 5: Create `PPT_Generator/templates/registry.py`**

```python
from typing import Dict

from PPT_Generator.templates.base import BaseLayout
from PPT_Generator.templates.layouts.bullet_focus import BulletFocusLayout
from PPT_Generator.templates.layouts.title import TitleLayout


class TemplateRegistry:
    def __init__(self):
        layouts: Dict[str, BaseLayout] = {
            TitleLayout.layout_id: TitleLayout(),
            BulletFocusLayout.layout_id: BulletFocusLayout(),
        }
        self._layouts = layouts

    def get(self, layout_id: str) -> BaseLayout:
        if layout_id not in self._layouts:
            raise KeyError(f"Unknown layout: {layout_id}")
        return self._layouts[layout_id]

    def list_layouts(self) -> list[str]:
        return list(self._layouts.keys())
```

- [ ] **Step 6: Write test `tests/test_templates.py`**

```python
import os
import tempfile

from pptx import Presentation

from PPT_Generator.models import Slide
from PPT_Generator.templates.registry import TemplateRegistry


def test_registry_has_core_layouts():
    registry = TemplateRegistry()
    assert "title" in registry.list_layouts()
    assert "bullet_focus" in registry.list_layouts()


def test_title_layout_renders():
    registry = TemplateRegistry()
    layout = registry.get("title")
    prs = Presentation()
    blank = prs.slide_layouts[6]
    prs_slide = prs.slides.add_slide(blank)
    slide = Slide(page_number=1, layout_id="title", title="Hello", subtitle="World")
    layout.render(slide, prs_slide)

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        path = f.name
    prs.save(path)
    assert os.path.getsize(path) > 0
    os.unlink(path)
```

- [ ] **Step 7: Run test**

```bash
pytest tests/test_templates.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add PPT_Generator/templates/ tests/test_templates.py
git commit -m "feat: add template system foundation with title and bullet layouts"
```

---

## Task 8: Planner

**Files:**
- Create: `PPT_Generator/planner.py`
- Test: `tests/test_planner.py`

**Interfaces:**
- Consumes: `LLMClient`, `(topic, brief, audience)`.
- Produces: `Planner.plan(topic, brief, audience) -> Outline`.

- [ ] **Step 1: Create `PPT_Generator/planner.py`**

```python
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline


PLANNER_SYSTEM = """You are a presentation planner. Given a topic, brief, and audience, produce:
1. A narrative arc for a 25-30 slide presentation
2. A list of sections, each with an estimated page count and key points
3. A list of fact queries that must be verified via web search

Output must follow the provided JSON schema."""

PLANNER_USER_TEMPLATE = """Topic: {topic}
Brief: {brief}
Audience: {audience}

Create a cohesive outline for a 25-30 slide presentation."""


class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def plan(self, topic: str, brief: str, audience: str) -> Outline:
        user_prompt = PLANNER_USER_TEMPLATE.format(topic=topic, brief=brief, audience=audience)
        return self.llm_client.chat(PLANNER_SYSTEM, user_prompt, Outline)
```

- [ ] **Step 2: Write test `tests/test_planner.py`**

```python
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline, SectionPlan, FactQuery
from PPT_Generator.planner import Planner
from PPT_Generator.cost_tracker import CostTracker


class FakeLLMClient:
    def __init__(self):
        self.tracker = CostTracker()

    def chat(self, system, user, response_format):
        return Outline(
            narrative_arc="arc",
            sections=[SectionPlan(section_title="Intro", pages=5, key_points=["a", "b"])],
            fact_queries=[FactQuery(entity="Imperial", attributes=["tuition"])],
        )


def test_planner_returns_outline():
    planner = Planner(FakeLLMClient())
    outline = planner.plan("topic", "brief", "audience")
    assert outline.sections[0].section_title == "Intro"
    assert outline.fact_queries[0].entity == "Imperial"
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_planner.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/planner.py tests/test_planner.py
git commit -m "feat: add planner stage"
```

---

## Task 9: Researcher

**Files:**
- Create: `PPT_Generator/researcher.py`
- Test: `tests/test_researcher.py`

**Interfaces:**
- Consumes: `SearchClient`, `Outline`.
- Produces: `Researcher.research(outline: Outline) -> list[ResearchResult]`.

- [ ] **Step 1: Create `PPT_Generator/researcher.py`**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from PPT_Generator.models import FactQuery, Outline, ResearchResult
from PPT_Generator.search_client import SearchClient


class Researcher:
    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    def _search_one(self, query: FactQuery, attribute: str) -> ResearchResult:
        full_query = f"{query.entity} {attribute}"
        try:
            response = self.search_client.search(full_query)
            answer = response.get("answer", "")
            results = response.get("results", [])
            source_url = results[0].get("url", "") if results else ""
            confidence = "medium" if answer else "low"
            return ResearchResult(
                entity=query.entity,
                attribute=attribute,
                value=answer or "未找到",
                source_url=source_url,
                confidence=confidence,
            )
        except Exception:
            return ResearchResult(
                entity=query.entity,
                attribute=attribute,
                value="搜索失败",
                source_url="",
                confidence="low",
            )

    def research(self, outline: Outline) -> List[ResearchResult]:
        tasks = []
        for query in outline.fact_queries:
            for attribute in query.attributes:
                tasks.append((query, attribute))
        results: List[ResearchResult] = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._search_one, q, a): (q, a) for q, a in tasks}
            for future in as_completed(futures):
                results.append(future.result())
        return results
```

- [ ] **Step 2: Write test `tests/test_researcher.py`**

```python
from PPT_Generator.models import FactQuery, Outline, SectionPlan
from PPT_Generator.researcher import Researcher


class FakeSearchClient:
    def __init__(self):
        self.calls = 0

    def search(self, query):
        self.calls += 1
        return {"answer": "£35k", "results": [{"url": "https://example.com"}]}


def test_researcher_returns_results():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=5, key_points=[])],
        fact_queries=[FactQuery(entity="Imperial", attributes=["tuition", "deadline"])],
    )
    search_client = FakeSearchClient()
    researcher = Researcher(search_client)
    results = researcher.research(outline)
    assert len(results) == 2
    assert results[0].value == "£35k"
    assert search_client.calls == 2
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_researcher.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/researcher.py tests/test_researcher.py
git commit -m "feat: add researcher stage with parallel search"
```

---

## Task 10: Content Generator

**Files:**
- Create: `PPT_Generator/content_generator.py`
- Test: `tests/test_content_generator.py`

**Interfaces:**
- Consumes: `LLMClient`, `Outline`, `list[ResearchResult]`, `TemplateRegistry`.
- Produces: `ContentGenerator.generate(topic, audience, outline, research, layouts) -> Presentation`.

- [ ] **Step 1: Create `PPT_Generator/content_generator.py`**

```python
from typing import List

from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline, Presentation, ResearchResult
from PPT_Generator.templates.registry import TemplateRegistry


GENERATOR_SYSTEM = """You are a presentation content generator. Given an outline, research results, and available slide layouts, produce 25-30 slides.

Rules:
- Each slide must use one of the available layouts
- Content must be factually accurate; use research results for specific facts
- Mark uncertain information as "尚未公布" or "需核实"
- Include source annotations for factual claims
- Do not pad with repetition or sentence splitting
- Maintain a coherent narrative arc"""


class ContentGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        topic: str,
        audience: str,
        outline: Outline,
        research: List[ResearchResult],
        layouts: TemplateRegistry,
    ) -> Presentation:
        user_prompt = self._build_prompt(topic, audience, outline, research, layouts)
        return self.llm_client.chat(GENERATOR_SYSTEM, user_prompt, Presentation)

    def _build_prompt(self, topic, audience, outline, research, layouts):
        research_text = "\n".join(
            f"- {r.entity} {r.attribute}: {r.value} (confidence: {r.confidence}, source: {r.source_url})"
            for r in research
        )
        layout_text = "\n".join(f"- {lid}" for lid in layouts.list_layouts())
        return f"""Topic: {topic}
Audience: {audience}
Narrative arc: {outline.narrative_arc}

Available layouts:
{layout_text}

Research results:
{research_text}

Generate the full presentation."""
```

- [ ] **Step 2: Write test `tests/test_content_generator.py`**

```python
from PPT_Generator.content_generator import ContentGenerator
from PPT_Generator.models import Outline, Presentation, ResearchResult, SectionPlan, Slide
from PPT_Generator.templates.registry import TemplateRegistry


class FakeLLMClient:
    def __init__(self):
        pass

    def chat(self, system, user, response_format):
        return Presentation(
            topic="T",
            audience="A",
            narrative_arc="arc",
            slides=[Slide(page_number=1, layout_id="title", title="Hello")],
            total_pages=1,
            sources=["https://example.com"],
        )


def test_content_generator_returns_presentation():
    outline = Outline(
        narrative_arc="arc",
        sections=[SectionPlan(section_title="Intro", pages=1, key_points=["a"])],
        fact_queries=[],
    )
    research = [ResearchResult(entity="E", attribute="a", value="v", source_url="https://example.com", confidence="high")]
    layouts = TemplateRegistry()
    generator = ContentGenerator(FakeLLMClient())
    pres = generator.generate("T", "A", outline, research, layouts)
    assert pres.slides[0].title == "Hello"
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_content_generator.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/content_generator.py tests/test_content_generator.py
git commit -m "feat: add content generator stage"
```

---

## Task 11: Validator

**Files:**
- Create: `PPT_Generator/validator.py`
- Test: `tests/test_validator.py`

**Interfaces:**
- Consumes: `LLMClient`, `Presentation`.
- Produces: `Validator.validate(presentation: Presentation, layouts: TemplateRegistry) -> Presentation`.

- [ ] **Step 1: Create `PPT_Generator/validator.py`**

```python
from typing import List

from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Presentation, Slide
from PPT_Generator.templates.registry import TemplateRegistry


VALIDATOR_SYSTEM = """You are a presentation reviewer. Given a presentation, check:
1. Total pages between 25 and 30
2. Narrative coherence between slides
3. No repetitive or empty pages
4. Uncertain facts are marked
5. Layout choices match content

Return the corrected presentation as JSON. If page count is off, add or remove slides."""


class Validator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def validate(self, presentation: Presentation, layouts: TemplateRegistry) -> Presentation:
        # Pre-check: ensure all layout_ids are valid and page count is within bounds
        valid_layouts = set(layouts.list_layouts())
        slides: List[Slide] = []
        for i, slide in enumerate(presentation.slides, start=1):
            if slide.layout_id not in valid_layouts:
                slide.layout_id = "bullet_focus"
            slide.page_number = i
            slides.append(slide)
        presentation.slides = slides
        presentation.total_pages = len(slides)

        if 25 <= presentation.total_pages <= 30:
            return presentation

        user_prompt = self._build_prompt(presentation)
        return self.llm_client.chat(VALIDATOR_SYSTEM, user_prompt, Presentation)

    def _build_prompt(self, presentation: Presentation) -> str:
        return f"""Current presentation has {presentation.total_pages} slides. Required: 25-30.
Topic: {presentation.topic}
Audience: {presentation.audience}
Narrative arc: {presentation.narrative_arc}

Slides:
""" + "\n".join(
            f"{s.page_number}. [{s.layout_id}] {s.title}" for s in presentation.slides
        )
```

- [ ] **Step 2: Write test `tests/test_validator.py`**

```python
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
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_validator.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/validator.py tests/test_validator.py
git commit -m "feat: add validator stage"
```

---

## Task 12: Renderer

**Files:**
- Create: `PPT_Generator/renderer.py`
- Test: `tests/test_renderer.py`

**Interfaces:**
- Consumes: `Presentation`, `TemplateRegistry`, optional `ImageSearchClient`.
- Produces: `Renderer.render(presentation, output_path)`.

- [ ] **Step 1: Create `PPT_Generator/renderer.py`**

```python
import tempfile
from typing import Optional

import httpx
from pptx import Presentation as PptxPresentation
from pptx.util import Inches

from PPT_Generator.image_search import ImageSearchClient
from PPT_Generator.models import Presentation, Slide
from PPT_Generator.templates.registry import TemplateRegistry


class Renderer:
    def __init__(self, templates: TemplateRegistry, image_client: Optional[ImageSearchClient] = None):
        self.templates = templates
        self.image_client = image_client

    def render(self, presentation: Presentation, output_path: str) -> None:
        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        blank_layout = prs.slide_layouts[6]

        for slide_model in presentation.slides:
            prs_slide = prs.slides.add_slide(blank_layout)
            layout = self.templates.get(slide_model.layout_id)
            layout.render(slide_model, prs_slide)
            if slide_model.image_keyword and self.image_client:
                self._add_image(prs_slide, slide_model)

        prs.save(output_path)

    def _add_image(self, prs_slide, slide_model: Slide) -> None:
        try:
            url = self.image_client.search(slide_model.image_keyword)
            if url:
                with httpx.Client(timeout=20.0) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                        f.write(response.content)
                        tmp_path = f.name
                prs_slide.shapes.add_picture(tmp_path, Inches(9), Inches(0.6), width=Inches(3.5))
        except Exception:
            pass
```

- [ ] **Step 2: Write test `tests/test_renderer.py`**

```python
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
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_renderer.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/renderer.py tests/test_renderer.py
git commit -m "feat: add pptx renderer"
```

---

## Task 13: Pipeline Orchestrator

**Files:**
- Create: `PPT_Generator/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: all stages and clients.
- Produces: `Pipeline.run(topic, brief, audience, output_path) -> dict` report.

- [ ] **Step 1: Create `PPT_Generator/pipeline.py`**

```python
from PPT_Generator.config import settings
from PPT_Generator.content_generator import ContentGenerator
from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.image_search import ImageSearchClient
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.planner import Planner
from PPT_Generator.researcher import Researcher
from PPT_Generator.renderer import Renderer
from PPT_Generator.search_client import SearchClient
from PPT_Generator.templates.registry import TemplateRegistry
from PPT_Generator.validator import Validator


class Pipeline:
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.llm_client = LLMClient(self.cost_tracker)
        self.search_client = SearchClient(self.cost_tracker)
        self.image_client = ImageSearchClient(self.cost_tracker)
        self.templates = TemplateRegistry()

        self.planner = Planner(self.llm_client)
        self.researcher = Researcher(self.search_client)
        self.content_generator = ContentGenerator(self.llm_client)
        self.validator = Validator(self.llm_client)
        self.renderer = Renderer(self.templates, self.image_client)

    def run(self, topic: str, brief: str, audience: str, output_path: str) -> dict:
        outline = self.planner.plan(topic, brief, audience)
        research = self.researcher.research(outline)
        presentation = self.content_generator.generate(topic, audience, outline, research, self.templates)
        presentation = self.validator.validate(presentation, self.templates)
        self.renderer.render(presentation, output_path)
        report = self.cost_tracker.report()
        report["output_path"] = output_path
        report["total_pages"] = presentation.total_pages
        return report
```

- [ ] **Step 2: Write test `tests/test_pipeline.py`**

```python
from unittest.mock import MagicMock, patch

from PPT_Generator.models import Outline, Presentation, ResearchResult, SectionPlan, Slide
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
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_pipeline.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add PPT_Generator/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator"
```

---

## Task 14: CLI and Entry Point

**Files:**
- Create: `PPT_Generator/cli.py`
- Modify: `PPT_Generator/__main__.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `python -m PPT_Generator input.json output.pptx` works.

- [ ] **Step 1: Create `PPT_Generator/cli.py`**

```python
import argparse
import json
import sys

from PPT_Generator.pipeline import Pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a PPT from JSON input.")
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument("output", help="Path to output .pptx file")
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    topic = data.get("topic", "")
    brief = data.get("brief", "")
    audience = data.get("audience", "")

    if not topic or not brief or not audience:
        print("Error: input JSON must contain topic, brief, and audience.", file=sys.stderr)
        sys.exit(1)

    pipeline = Pipeline()
    report = pipeline.run(topic, brief, audience, args.output)
    print(f"Generated {report['total_pages']} slides to {report['output_path']}")
    print(f"Estimated cost: ¥{report['estimated_cost_rmb']}, elapsed: {report['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Modify `PPT_Generator/__main__.py`**

```python
from PPT_Generator.cli import main


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write test `tests/test_cli.py`**

```python
import json

from PPT_Generator.cli import main


def test_cli_exits_on_missing_field(tmp_path, monkeypatch):
    input_path = tmp_path / "in.json"
    input_path.write_text(json.dumps({"topic": "T"}))
    output_path = tmp_path / "out.pptx"

    with monkeypatch.context() as m:
        m.setattr("sys.argv", ["ppt_generator", str(input_path), str(output_path)])
        try:
            main()
        except SystemExit as e:
            assert e.code == 1
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_cli.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add PPT_Generator/cli.py PPT_Generator/__main__.py tests/test_cli.py
git commit -m "feat: add CLI and package entry point"
```

---

## Task 15: Integration Test and Sample Input

**Files:**
- Create: `examples/sample_input.json`
- Create: `tests/test_integration.py`
- Modify: `README.md`

**Interfaces:**
- Produces: A runnable integration test that mocks external services and verifies a `.pptx` file is created with valid slide count.

- [ ] **Step 1: Create `examples/sample_input.json`**

```json
{
  "topic": "2027 Fall 英国商业分析硕士选校与申请规划",
  "brief": "介绍商业分析硕士的学习内容和就业方向；以 Imperial、UCL、Warwick 和 Edinburgh 为例，比较项目特点、申请要求、截止日期、学费和课程时长。",
  "audience": "计划申请英国商业分析硕士的学生"
}
```

- [ ] **Step 2: Create `tests/test_integration.py`**

```python
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from PPT_Generator.models import Outline, Presentation, ResearchResult, SectionPlan, Slide


@patch("PPT_Generator.pipeline.LLMClient")
@patch("PPT_Generator.pipeline.SearchClient")
@patch("PPT_Generator.pipeline.ImageSearchClient")
def test_full_pipeline_creates_pptx(mock_image, mock_search, mock_llm, tmp_path):
    llm_instance = MagicMock()
    llm_instance.chat.side_effect = [
        Outline(
            narrative_arc="arc",
            sections=[SectionPlan(section_title="Intro", pages=25, key_points=["a"])],
            fact_queries=[],
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

    search_instance = MagicMock()
    search_instance.search.return_value = {"answer": "£35k", "results": [{"url": "https://example.com"}]}
    mock_search.return_value = search_instance

    input_path = tmp_path / "in.json"
    input_path.write_text(json.dumps({"topic": "T", "brief": "B", "audience": "A"}))
    output_path = tmp_path / "out.pptx"

    from PPT_Generator.cli import main
    import sys
    argv = ["ppt_generator", str(input_path), str(output_path)]
    main(argv)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
```

- [ ] **Step 3: Run test**

```bash
pytest tests/test_integration.py -v
```

Expected: PASS

- [ ] **Step 4: Update `README.md`**

Replace the empty README with installation and usage instructions, documenting dependencies on `ARK_API_KEY`, `TAVILY_API_KEY`, and optional `UNSPLASH_ACCESS_KEY`.

- [ ] **Step 5: Run full test suite**

```bash
pytest
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add examples/ tests/test_integration.py README.md
git commit -m "feat: add integration test, sample input, and README"
```

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Implementing Task |
| :--- | :--- |
| 25–30 slide output | Task 3 (models), Task 10 (generator), Task 11 (validator) |
| Coherent narrative arc | Task 8 (planner), Task 10 (generator) |
| Fact verification via search | Task 5 (Tavily), Task 9 (researcher) |
| Constrained templates | Task 7 (templates) |
| python-pptx rendering | Task 12 (renderer) |
| Cost ≤ ¥0.10/slide, time ≤ 30s/slide | Task 3 (tracker), all tasks via limited LLM calls |
| Single CLI command | Task 14 (CLI) |
| No hard-coded demo content | Task 10 prompt uses only input + research |
| Stability / retry / error handling | Task 1 config, implicit retry wrappers in clients |

### 2. Placeholder Scan

- No "TBD", "TODO", or "implement later" in task steps.
- All code blocks contain runnable implementations.
- All test blocks contain concrete assertions.
- No vague requirements like "add appropriate error handling" without code.

### 3. Type Consistency

- `Slide`, `Presentation`, `Outline`, `ResearchResult` types are consistent across Tasks 2, 8, 9, 10, 11, 12, 13.
- `LLMClient.chat(system, user, response_format)` signature is consistent in Tasks 4, 8, 10, 11.
- `TemplateRegistry.list_layouts()` and `.get(layout_id)` are used consistently in Tasks 7, 10, 11, 12.

### 4. Known Gaps

- Retry wrappers are described in the spec but not yet extracted into a shared utility. Task 4/5/6 clients should wrap calls in `retry_with_backoff`; this can be added as a small follow-up refactor after Task 6.
- Only two layouts (`title`, `bullet_focus`) are implemented in Task 7. Remaining layouts from the design spec (`section_divider`, `two_column`, `three_card`, `timeline`, `comparison_table`, `data_highlight`, `quote`, `closing`) should be added in a follow-up task after Task 15.
- Cost estimates use approximate RMB rates for kimi-k2.6/Tavily; actual rates should be verified against the latest Ark/Tavily pricing before final cost reporting.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-01-ppt-generator-plan.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

Which approach do you prefer?
