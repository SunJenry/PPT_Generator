from typing import List, Optional

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
    table: Optional[List[List[str]]] = None
    image_keyword: Optional[str] = None
    image_url: Optional[str] = None
    source_notes: List[str] = []
    notes: Optional[str] = None


class Presentation(BaseModel):
    topic: str
    audience: str
    narrative_arc: str
    slides: List[Slide]
    total_pages: int
    sources: List[str]
