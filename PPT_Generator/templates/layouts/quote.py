"""Quote slide layout — impactful quote or takeaway."""

from pptx.slide import Slide as PptxSlide
from pptx.util import Inches, Pt

from PPT_Generator.design import (
    ACCENT,
    CONTENT_BOTTOM,
    CONTENT_WIDTH,
    SAFE_LEFT,
    SIZE_QUOTE,
    SIZE_SMALL,
    TEXT_MAIN,
    TEXT_MUTED,
    TITLE_Y,
    add_textbox,
    draw_footer,
    draw_header,
    estimate_text_height,
    truncate_text,
)
from PPT_Generator.models import Slide
from PPT_Generator.templates.base import BaseLayout


class QuoteLayout(BaseLayout):
    layout_id = "quote"

    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        draw_header(prs_slide, section_title=slide.section_title)
        draw_footer(prs_slide, slide.page_number, total_pages)

        # ── Large decorative quotation mark ──
        quote_y = TITLE_Y + Inches(0.3)
        add_textbox(
            prs_slide, SAFE_LEFT, quote_y, Inches(1.5), Inches(1.0),
            text='"',
            font_size=Pt(72), color=ACCENT, bold=True,
        )

        # ── Quote text (dynamic height) ──
        quote = slide.quote_text or slide.title
        quote_text_y = quote_y + Inches(0.5)
        quote_height = estimate_text_height(quote, SIZE_QUOTE.pt, Inches(10.0).inches)
        quote_height = max(quote_height, Inches(1.0))

        tb, _, _ = add_textbox(
            prs_slide, SAFE_LEFT + Inches(1.0), quote_text_y, Inches(10.0), quote_height,
            text=truncate_text(quote, 250),
            font_size=SIZE_QUOTE, color=TEXT_MAIN,
        )
        tb.text_frame.word_wrap = True

        after_quote = quote_text_y + quote_height + Inches(0.2)

        # ── Accent line ──
        bar = prs_slide.shapes.add_shape(
            1, SAFE_LEFT + Inches(1.0), after_quote, Inches(2.0), Pt(3),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()

        after_line = after_quote + Inches(0.2)

        # ── Attribution ──
        if slide.quote_author:
            add_textbox(
                prs_slide, SAFE_LEFT + Inches(1.0), after_line, Inches(10.0), Inches(0.6),
                text=f"— {slide.quote_author}",
                font_size=SIZE_SMALL, color=TEXT_MUTED,
            )

        # ── Context ──
        if slide.notes:
            add_textbox(
                prs_slide, SAFE_LEFT + Inches(1.0), after_line + Inches(0.5), Inches(10.0), Inches(0.8),
                text=slide.notes,
                font_size=Pt(13), color=TEXT_MUTED,
            )
