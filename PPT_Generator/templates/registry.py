from typing import Dict

from PPT_Generator.templates.base import BaseLayout
from PPT_Generator.templates.layouts.bullet_focus import BulletFocusLayout
from PPT_Generator.templates.layouts.title import TitleLayout


class TemplateRegistry:
    def __init__(self):
        layouts: Dict[str, BaseLayout] = {
            TitleLayout.layout_id: TitleLayout(),
            BulletFocusLayout.layout_id: BulletFocusLayout(),
        }
        self._layouts = layouts

    def get(self, layout_id: str) -> BaseLayout:
        if layout_id not in self._layouts:
            raise KeyError(f"Unknown layout: {layout_id}")
        return self._layouts[layout_id]

    def list_layouts(self) -> list[str]:
        return list(self._layouts.keys())
