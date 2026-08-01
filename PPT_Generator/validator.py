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
