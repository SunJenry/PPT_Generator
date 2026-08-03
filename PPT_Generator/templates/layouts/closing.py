"""Closing slide — final wrap-up and thank you."""

from pptx.slide import Slide as PptxSlide
from pptx.util import Inches, Pt

from PPT_Generator.design import (
    ACCENT,
    CONTENT_WIDTH,
    PRIMARY,
    SAFE_LEFT,
    SIZE_BODY_LG,
    SIZE_SMALL,
    SIZE_TITLE_COVER,
    TEXT_MUTED,
    WHITE,
    add_textbox,
    truncate_text,
)
from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout


class ClosingLayout(BaseLayout):
    layout_id = "closing"

    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        # ── Full navy background ──
        bg = prs_slide.shapes.add_shape(
            1, Inches(0), Inches(0), Inches(13.333), Inches(7.5),
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = PRIMARY
        bg.line.fill.background()

        # ── Gold accent bar ──
        bar = prs_slide.shapes.add_shape(
            1, Inches(5.5), Inches(3.0), Inches(2.5), Pt(4),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()

        # ── Title ──
        add_textbox(
            prs_slide, Inches(1.5), Inches(2.0), Inches(10.333), Inches(1.5),
            text=slide.title,
            font_size=SIZE_TITLE_COVER, color=WHITE, bold=True,
        )

        # ── Closing text ──
        closing = slide.closing_text or ""
        if closing:
            add_textbox(
                prs_slide, Inches(1.5), Inches(3.5), Inches(10.333), Inches(1.0),
                text=truncate_text(closing, 200),
                font_size=SIZE_BODY_LG, color=TEXT_MUTED,
            )

        # ── Subtitle / "Thank You" ──
        if slide.subtitle:
            add_textbox(
                prs_slide, Inches(1.5), Inches(5.0), Inches(10.333), Inches(0.6),
                text=slide.subtitle,
                font_size=SIZE_SMALL, color=TEXT_MUTED,
            )
