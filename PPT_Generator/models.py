from typing import List, Optional

from pydantic import BaseModel, Field


class FactQuery(BaseModel):
    entity: str
    attributes: List[str]


class ResearchResult(BaseModel):
    entity: str
    attribute: str
    value: str
    source_url: str
    confidence: str = Field(pattern=r"^(high|medium|low)$")


class SectionPlan(BaseModel):
    section_title: str
    pages: int
    key_points: List[str]


class Outline(BaseModel):
    narrative_arc: str
    sections: List[SectionPlan]
    fact_queries: List[FactQuery]


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
