from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline, Presentation
from PPT_Generator.templates.registry import TemplateRegistry


GENERATOR_SYSTEM = """You are a presentation content generator. Given an outline and available slide layouts, produce 25-30 slides.

Rules:
- Each slide must use one of the available layouts
- Factual claims (deadlines, tuition, fees, requirements, policies) must be verified with the web_search tool before being stated; do not rely on memory for specific numbers or dates
- After searching, cite the source: put the source URL or official page name into the slide's source_notes field for every factual claim
- Information that is not yet published must be marked explicitly as "Not yet published"; never guess from past years
- Do not pad with repetition or sentence splitting
- Maintain a coherent narrative arc
- Write content in Chinese (the audience is Chinese-speaking), keep layout_id values in English"""


class ContentGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        topic: str,
        audience: str,
        outline: Outline,
        layouts: TemplateRegistry,
    ) -> Presentation:
        user_prompt = self._build_prompt(topic, audience, outline, layouts)
        return self.llm_client.chat(GENERATOR_SYSTEM, user_prompt, Presentation, use_search=True)

    def _build_prompt(self, topic, audience, outline, layouts):
        layout_text = "\n".join(f"- {lid}" for lid in layouts.list_layouts())
        sections_text = "\n".join(
            f"- {s.section_title} ({s.pages} pages): {', '.join(s.key_points)}"
            for s in outline.sections
        )
        return f"""Topic: {topic}
Audience: {audience}
Narrative arc: {outline.narrative_arc}

Planned sections:
{sections_text}

Available layouts:
{layout_text}

Generate the full presentation. Use web_search to verify factual claims, and cite sources in source_notes."""
