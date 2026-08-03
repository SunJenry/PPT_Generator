"""Re-exported from PPT_Generator.design for backward compatibility."""

from PPT_Generator.design import (  # noqa: F401
    ACCENT,
    BACKGROUND,
    DIVIDER,
    HEADER_BG,
    LIGHT_BG,
    PRIMARY,
    SECONDARY,
    SUCCESS,
    TEXT_MAIN,
    TEXT_MUTED,
    WARNING,
    WHITE,
    BODY_FONT,
    TITLE_FONT,
    WESTERN_FONT,
    SAFE_LEFT,
    SAFE_RIGHT,
    SAFE_TOP,
    SAFE_BOTTOM,
    CONTENT_WIDTH,
    CONTENT_MAX_HEIGHT,
    SLIDE_HEIGHT,
    SLIDE_WIDTH,
)

# Legacy aliases
COLORS = {
    "primary": PRIMARY,
    "accent": ACCENT,
    "background": BACKGROUND,
    "text": TEXT_MAIN,
    "muted": TEXT_MUTED,
}
FONTS = {
    "chinese": BODY_FONT,
    "western": WESTERN_FONT,
}
MARGINS = {
    "left": SAFE_LEFT,
    "right": SAFE_RIGHT,
    "top": SAFE_TOP,
    "bottom": SAFE_BOTTOM,
}
