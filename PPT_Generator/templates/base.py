from abc import ABC, abstractmethod
from typing import Optional

from pptx.slide import Slide as PptxSlide

from PPT_Generator.models import Slide


class BaseLayout(ABC):
    layout_id: str

    @abstractmethod
    def render(self, slide: Slide, prs_slide: PptxSlide, total_pages: int = 0) -> None:
        raise NotImplementedError
