from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SectionPlan(BaseModel):
    section_title: str
    pages: int
    key_points: List[str]


class Outline(BaseModel):
    narrative_arc: str
    sections: List[SectionPlan]


class Slide(BaseModel):
    page_number: int
    layout_id: str
    title: str
    subtitle: Optional[str] = None
    bullets: List[str] = []

    # ── Layout-specific content fields ──
    # section_divider
    section_number: Optional[int] = None
    section_title: Optional[str] = None

    # two_column
    left_column: List[str] = []
    right_column: List[str] = []

    # three_card
    cards: List[Dict[str, str]] = []         # [{"title": "...", "body": "..."}, ...]

    # timeline
    timeline_items: List[Dict[str, str]] = []  # [{"date": "2026-09", "event": "..."}, ...]

    # data_highlight
    highlight_number: Optional[str] = None    # e.g. "85%", "£35,000"
    highlight_label: Optional[str] = None     # short description

    # quote
    quote_text: Optional[str] = None
    quote_author: Optional[str] = None

    # closing
    closing_text: Optional[str] = None

    # table (comparison_table layout)
    table: Optional[List[List[str]]] = None

    # images
    image_keyword: Optional[str] = None
    image_url: Optional[str] = None

    # metadata
    source_notes: List[str] = []
    notes: Optional[str] = None


class Presentation(BaseModel):
    topic: str
    audience: str
    narrative_arc: str
    slides: List[Slide]
    total_pages: int
    sources: List[str]
