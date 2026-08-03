"""Standard content slide layout — flow layout, no hardcoded positions."""

from pptx.slide import Slide as PptxSlide
from pptx.util import Inches, Pt

from PPT_Generator.design import (
    CONTENT_BOTTOM,
    CONTENT_WIDTH,
    SAFE_LEFT,
    TEXT_MUTED,
    add_textbox,
    draw_bullet_body,
    draw_footer,
    draw_header,
    draw_slide_title,
    truncate_text,
)
from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout

MAX_BULLETS = 5


class ContentLayout(BaseLayout):
    layout_id = "content"

    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        # ── Fixed-position elements (always safe) ──
        draw_footer(prs_slide, slide.page_number, total_pages)

        # Reserve space for source notes if present
        body_bottom = CONTENT_BOTTOM - Inches(0.35) if slide.source_notes else CONTENT_BOTTOM

        # ── Flow chain: each step returns where the next should start ──
        y = draw_header(prs_slide, section_title=slide.section_title)
        y = draw_slide_title(prs_slide, slide.title, y=y)
        draw_bullet_body(prs_slide, slide.bullets, start_y=y, max_y=body_bottom, max_bullets=MAX_BULLETS)

        # ── Source notes below bullets ──
        if slide.source_notes:
            add_textbox(
                prs_slide,
                SAFE_LEFT, body_bottom + Inches(0.05), CONTENT_WIDTH, Inches(0.25),
                text=f"来源: {slide.source_notes[0]}",
                font_size=Pt(9),
                color=TEXT_MUTED,
            )
