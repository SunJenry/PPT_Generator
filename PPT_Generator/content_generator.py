from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline, Presentation
from PPT_Generator.templates.registry import TemplateRegistry


GENERATOR_SYSTEM = """You are a presentation content generator. Given an outline and available slide layouts, produce 25-30 slides.

**CRITICAL — Token Budget**: You have limited output tokens. The 25-30 slide JSON is large (~8000+ chars). Do at MOST 2 rounds of web_search, then IMMEDIATELY output the full JSON. Do not output search planning thoughts — go straight from search results to the JSON object. Mark unverified facts as "Not yet published" — do NOT keep searching to verify everything. The JSON output MUST be your top priority.

## Available Layouts

Use these layout_id values. Choose the right layout for each slide's content type:

| layout_id | Best for | Key fields |
|---|---|---|
| `title_slide` | Cover page | title, subtitle |
| `section_divider` | Starting a new section/chapter | title, section_number, section_title |
| `content` | Standard content with bullet points | title, bullets |
| `two_column` | Comparison, pros/cons, two perspectives | title, left_column[], right_column[] |
| `three_card` | Three key points, features, or options | title, cards[{"title","body"}] |
| `timeline` | Chronological sequence, milestones | title, timeline_items[{"date","event"}] |
| `comparison_table` | Side-by-side comparison of multiple items | title, table (first row = header) |
| `data_highlight` | Key statistic, cost, or important number | title, highlight_number, highlight_label |
| `quote` | Important quote or takeaway | quote_text, quote_author |
| `closing` | Final slide — summary and thank you | title, closing_text |

## Layout Usage Guidelines

- Slide 1 must be `title_slide`
- After each major section change, insert a `section_divider` slide (2-4 total)
- Use `content` for ~40% of slides — these carry the main narrative
- Use `two_column` for comparisons (e.g. comparing schools, countries, options)
- Use `three_card` for presenting 3 parallel ideas, features, or recommendations
- Use `timeline` for application timelines, historical context, or step-by-step processes (4-8 items)
- Use `comparison_table` when comparing 3+ items across multiple dimensions (tuition, duration, requirements)
- Use `data_highlight` sparingly (1-3 times) for impactful numbers — tuition totals, acceptance rates, salary figures
- Use `quote` for 1-2 important takeaways or expert advice
- Last slide must be `closing`

## Content Rules

- Factual claims (deadlines, tuition, fees, requirements, policies) must be verified with the web_search tool before being stated; do not rely on memory for specific numbers or dates
- After searching, cite the source: put the source URL or official page name into the slide's source_notes field for every factual claim
- Information that is not yet published must be marked explicitly as "Not yet published"; never guess from past years
- Do not pad with repetition or sentence splitting
- Maintain a coherent narrative arc
- Write content in Chinese (the audience is Chinese-speaking), keep layout_id values in English
- Each slide should have meaningful, substantial content — not just 1-2 words
- For `timeline` layout, provide 4-8 items with dates and descriptions
- For `comparison_table`, first row should be column headers
- For `three_card`, each card should have a title and a body (2-3 sentences)
- For `content` slides, provide 3-5 substantive bullet points"""



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

Available layouts: {', '.join(layouts.list_layouts())}

Layout guide:
- Slide 1: title_slide (cover), last slide: closing
- Every 5-8 slides: section_divider to mark a new section
- ~40% content slides for the main narrative
- Use two_column for comparisons, three_card for parallel ideas
- Use timeline for chronological sequences, comparison_table for multi-item comparisons
- Use data_highlight (1-3 times) for key numbers
- Use quote (1-2 times) for important takeaways

Generate the full presentation. Use web_search to verify factual claims, and cite sources in source_notes."""
