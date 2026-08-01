from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

COLORS = {
    "primary": RGBColor(0x1E, 0x3A, 0x5F),
    "accent": RGBColor(0x4A, 0x90, 0xD9),
    "background": RGBColor(0xFF, 0xFF, 0xFF),
    "text": RGBColor(0x33, 0x33, 0x33),
    "muted": RGBColor(0x66, 0x66, 0x66),
}

FONTS = {
    "chinese": "Microsoft YaHei",
    "western": "Arial",
}

MARGINS = {
    "left": Inches(0.8),
    "right": Inches(0.8),
    "top": Inches(0.6),
    "bottom": Inches(0.6),
}

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
