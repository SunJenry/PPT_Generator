"""Data highlight layout — big number / key statistic with auto-shrink."""

from pptx.slide import Slide as PptxSlide
from pptx.util import Inches, Pt

from PPT_Generator.design import (
    ACCENT,
    CONTENT_BOTTOM,
    CONTENT_WIDTH,
    SAFE_LEFT,
    SECONDARY,
    SIZE_HIGHLIGHT,
    SIZE_SMALL,
    TEXT_MAIN,
    TEXT_MUTED,
    add_fitted_textbox,
    add_textbox,
    draw_decorative_circle,
    draw_footer,
    draw_header,
    draw_slide_title,
    truncate_text,
)
from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout


class DataHighlightLayout(BaseLayout):
    layout_id = "data_highlight"

    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        draw_header(prs_slide, section_title=slide.section_title)
        draw_footer(prs_slide, slide.page_number, total_pages)

        # ── Slide title (dynamic height) ──
        body_y = draw_slide_title(prs_slide, slide.title)

        # ── Left accent bar ──
        bar = prs_slide.shapes.add_shape(
            1, SAFE_LEFT + Inches(0.5), body_y, Pt(4), CONTENT_BOTTOM - body_y,
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()

        # ── Decorative circle ──
        draw_decorative_circle(prs_slide, Inches(9.0), Inches(2.0), Inches(3.0), SECONDARY)

        # ── Big highlight number (auto-shrink to stay single-line) ──
        number_text = slide.highlight_number or "—"
        number_y = body_y + Inches(0.3)
        add_fitted_textbox(
            prs_slide, SAFE_LEFT + Inches(1.0), number_y, Inches(7), Inches(1.5),
            text=number_text,
            start_font_size=SIZE_HIGHLIGHT,
            min_font_size=Pt(24),
            color=ACCENT,
            bold=True,
        )

        # ── Label below the number ──
        if slide.highlight_label:
            label_y = number_y + Inches(1.3)
            add_textbox(
                prs_slide, SAFE_LEFT + Inches(1.0), label_y, Inches(7), Inches(0.6),
                text=slide.highlight_label,
                font_size=SIZE_SMALL, color=TEXT_MUTED,
            )

        # ── Context/notes on the right ──
        if slide.notes:
            add_textbox(
                prs_slide, Inches(8.5), CONTENT_BOTTOM - Inches(1.3), Inches(4.0), Inches(1.2),
                text=truncate_text(slide.notes, 200),
                font_size=Pt(13), color=TEXT_MAIN,
            )
