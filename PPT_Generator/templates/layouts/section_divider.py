"""Section divider slide — marks the start of a new chapter."""

from pptx.slide import Slide as PptxSlide
from pptx.util import Inches, Pt

from PPT_Generator.design import (
    ACCENT,
    BACKGROUND,
    CONTENT_WIDTH,
    PRIMARY,
    SAFE_LEFT,
    SIZE_SECTION,
    SIZE_SMALL,
    TEXT_MUTED,
    WHITE,
    add_textbox,
    draw_decorative_circle,
)
from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout


class SectionDividerLayout(BaseLayout):
    layout_id = "section_divider"

    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        # ── Full-width navy background ──
        bg = prs_slide.shapes.add_shape(
            1, Inches(0), Inches(0), Inches(13.333), Inches(7.5),
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = PRIMARY
        bg.line.fill.background()

        # ── Decorative gold bar ──
        bar = prs_slide.shapes.add_shape(
            1, Inches(0), Inches(3.2), Inches(13.333), Pt(4),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()

        # ── Decorative circles ──
        draw_decorative_circle(prs_slide, Inches(10.5), Inches(4.5), Inches(3.0), ACCENT)

        # ── Section number ──
        if slide.section_number:
            add_textbox(
                prs_slide, SAFE_LEFT, Inches(1.5), Inches(3), Inches(1.0),
                text=f"0{slide.section_number}" if slide.section_number < 10 else str(slide.section_number),
                font_size=Pt(60),
                color=ACCENT,
                bold=True,
            )

        # ── Section title ──
        add_textbox(
            prs_slide, SAFE_LEFT, Inches(3.6), CONTENT_WIDTH, Inches(1.2),
            text=slide.title,
            font_size=SIZE_SECTION,
            color=WHITE,
            bold=True,
        )

        # ── Subtitle ──
        if slide.subtitle:
            add_textbox(
                prs_slide, SAFE_LEFT, Inches(4.8), Inches(8), Inches(0.6),
                text=slide.subtitle,
                font_size=SIZE_SMALL,
                color=TEXT_MUTED,
            )
