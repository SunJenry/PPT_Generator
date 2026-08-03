from typing import Dict, List

from PPT_Generator.templates.base import BaseLayout
from PPT_Generator.templates.layouts.closing import ClosingLayout
from PPT_Generator.templates.layouts.comparison_table import ComparisonTableLayout
from PPT_Generator.templates.layouts.content import ContentLayout
from PPT_Generator.templates.layouts.data_highlight import DataHighlightLayout
from PPT_Generator.templates.layouts.quote import QuoteLayout
from PPT_Generator.templates.layouts.section_divider import SectionDividerLayout
from PPT_Generator.templates.layouts.three_card import ThreeCardLayout
from PPT_Generator.templates.layouts.timeline import TimelineLayout
from PPT_Generator.templates.layouts.title_slide import TitleSlideLayout
from PPT_Generator.templates.layouts.two_column import TwoColumnLayout


class TemplateRegistry:
    def __init__(self):
        layouts: Dict[str, BaseLayout] = {
            TitleSlideLayout.layout_id: TitleSlideLayout(),
            SectionDividerLayout.layout_id: SectionDividerLayout(),
            ContentLayout.layout_id: ContentLayout(),
            TwoColumnLayout.layout_id: TwoColumnLayout(),
            ThreeCardLayout.layout_id: ThreeCardLayout(),
            TimelineLayout.layout_id: TimelineLayout(),
            ComparisonTableLayout.layout_id: ComparisonTableLayout(),
            DataHighlightLayout.layout_id: DataHighlightLayout(),
            QuoteLayout.layout_id: QuoteLayout(),
            ClosingLayout.layout_id: ClosingLayout(),
        }
        self._layouts = layouts

    def get(self, layout_id: str) -> BaseLayout:
        if layout_id not in self._layouts:
            raise KeyError(f"Unknown layout: {layout_id}")
        return self._layouts[layout_id]

    def list_layouts(self) -> List[str]:
        return list(self._layouts.keys())
