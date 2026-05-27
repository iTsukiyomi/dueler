from dataclasses import dataclass
from typing import Tuple, Dict

Color = Tuple[int, int, int]

@dataclass
class ThemePalette:
    name: str
    frame_dark: Color
    frame_mid: Color
    panel_bg: Color
    panel_bg_dark: Color
    text_dark: Color
    text_mid: Color
    text_light: Color
    header_bg: Color
    header_text: Color
    hp_green: Color = (80, 200, 72)
    hp_yellow: Color = (248, 200, 48)
    hp_red: Color = (240, 72, 56)
    hp_bg: Color = (56, 56, 56)
    hp_border: Color = (40, 40, 40)
    font_hint: str = "sans"

_PALETTES: Dict[str, ThemePalette] = {
    "firered": ThemePalette(
        name="firered",
        frame_dark=(120, 48, 32),
        frame_mid=(224, 88, 64),
        panel_bg=(248, 244, 232),
        panel_bg_dark=(232, 220, 200),
        text_dark=(48, 40, 32),
        text_mid=(120, 100, 80),
        text_light=(180, 160, 140),
        header_bg=(224, 88, 64),
        header_text=(255, 255, 255),
        font_hint="pixel"
    ),
    "heartgold": ThemePalette(
        name="heartgold",
        frame_dark=(100, 80, 40),
        frame_mid=(200, 160, 80),
        panel_bg=(250, 248, 240),
        panel_bg_dark=(235, 225, 205),
        text_dark=(60, 50, 40),
        text_mid=(140, 120, 90),
        text_light=(185, 175, 155),
        header_bg=(200, 160, 80),
        header_text=(255, 255, 255),
        font_hint="pixel"
    ),
    "platinum": ThemePalette(
        name="platinum",
        frame_dark=(48, 56, 64),
        frame_mid=(112, 128, 144),
        panel_bg=(240, 244, 248),
        panel_bg_dark=(216, 224, 232),
        text_dark=(32, 40, 48),
        text_mid=(96, 112, 128),
        text_light=(160, 176, 192),
        header_bg=(112, 128, 144),
        header_text=(255, 255, 255),
        font_hint="pixel"
    ),
    "black": ThemePalette(
        name="black",
        frame_dark=(16, 16, 16),
        frame_mid=(48, 48, 48),
        panel_bg=(32, 32, 32),
        panel_bg_dark=(24, 24, 24),
        text_dark=(255, 255, 255),
        text_mid=(180, 180, 180),
        text_light=(100, 100, 100),
        header_bg=(16, 16, 16),
        header_text=(255, 255, 255),
        font_hint="pixel"
    ),
    "x": ThemePalette(
        name="x",
        frame_dark=(48, 80, 112),
        frame_mid=(96, 144, 192),
        panel_bg=(240, 248, 255),
        panel_bg_dark=(208, 224, 240),
        text_dark=(32, 48, 64),
        text_mid=(80, 112, 144),
        text_light=(144, 176, 208),
        header_bg=(48, 80, 112),
        header_text=(255, 255, 255),
        font_hint="sans"
    ),
    "sun": ThemePalette(
        name="sun",
        frame_dark=(220, 100, 40),
        frame_mid=(248, 160, 72),
        panel_bg=(255, 250, 240),
        panel_bg_dark=(248, 230, 210),
        text_dark=(80, 48, 24),
        text_mid=(160, 112, 72),
        text_light=(216, 180, 144),
        header_bg=(248, 160, 72),
        header_text=(255, 255, 255),
        font_hint="sans"
    ),
    "sword": ThemePalette(
        name="sword",
        frame_dark=(16, 48, 96),
        frame_mid=(32, 96, 192),
        panel_bg=(250, 252, 255),
        panel_bg_dark=(224, 235, 250),
        text_dark=(16, 32, 64),
        text_mid=(64, 96, 144),
        text_light=(160, 180, 210),
        header_bg=(32, 96, 192),
        header_text=(255, 255, 255),
        font_hint="sans"
    ),
    "scarlet": ThemePalette(
        name="scarlet",
        frame_dark=(144, 24, 40),
        frame_mid=(220, 40, 60),
        panel_bg=(255, 245, 245),
        panel_bg_dark=(245, 220, 220),
        text_dark=(64, 16, 24),
        text_mid=(160, 64, 80),
        text_light=(210, 150, 160),
        header_bg=(220, 40, 60),
        header_text=(255, 255, 255),
        font_hint="sans"
    )
}

DEFAULT_PALETTE = _PALETTES["firered"]

def get_palette(theme: str) -> ThemePalette:
    theme = theme.lower().strip()
    return _PALETTES.get(theme, DEFAULT_PALETTE)
