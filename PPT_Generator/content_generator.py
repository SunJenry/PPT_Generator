from typing import List

from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline, Presentation, ResearchResult
from PPT_Generator.templates.registry import TemplateRegistry


GENERATOR_SYSTEM = """You are a presentation content generator. Given an outline, research results, and available slide layouts, produce 25-30 slides.

Rules:
- Each slide must use one of the available layouts
- Content must be factually accurate; use research results for specific facts
- Mark uncertain information as "Not yet published" or "To be verified"
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
