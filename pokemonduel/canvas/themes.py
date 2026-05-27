from dataclasses import dataclass
from typing import Tuple

Color = Tuple[int, int, int]

@dataclass
class ThemePalette:
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
    font_hint: str = "sans" # "sans", "pixel", etc.

def get_palette(gen: int, theme: str) -> ThemePalette:
    theme = theme.lower()
    if gen == 1:
        # Gen 1: GameBoy Monochrome Green
        if theme == "dark":
            return ThemePalette(
                frame_dark=(15, 56, 15),
                frame_mid=(48, 98, 48),
                panel_bg=(15, 56, 15),
                panel_bg_dark=(4, 30, 4),
                text_dark=(155, 188, 15),
                text_mid=(139, 172, 15),
                text_light=(48, 98, 48),
                header_bg=(155, 188, 15),
                header_text=(15, 56, 15),
                font_hint="pixel"
            )
        else:
            return ThemePalette(
                frame_dark=(15, 56, 15),
                frame_mid=(48, 98, 48),
                panel_bg=(155, 188, 15),
                panel_bg_dark=(139, 172, 15),
                text_dark=(15, 56, 15),
                text_mid=(48, 98, 48),
                text_light=(139, 172, 15),
                header_bg=(15, 56, 15),
                header_text=(155, 188, 15),
                font_hint="pixel"
            )
    elif gen == 2:
        # Gen 2: GameBoy Color / Crystal
        if theme == "dark":
            return ThemePalette(
                frame_dark=(24, 24, 24),
                frame_mid=(60, 60, 100),
                panel_bg=(40, 40, 50),
                panel_bg_dark=(24, 24, 32),
                text_dark=(240, 240, 240),
                text_mid=(200, 200, 200),
                text_light=(120, 120, 120),
                header_bg=(40, 80, 160),
                header_text=(255, 255, 255),
                font_hint="pixel"
            )
        else:
            return ThemePalette(
                frame_dark=(40, 40, 40),
                frame_mid=(100, 100, 160),
                panel_bg=(248, 248, 248),
                panel_bg_dark=(224, 224, 224),
                text_dark=(32, 32, 32),
                text_mid=(80, 80, 80),
                text_light=(140, 140, 140),
                header_bg=(80, 120, 200),
                header_text=(255, 255, 255),
                font_hint="pixel"
            )
    elif gen == 3:
        # Gen 3: GBA Ruby/Sapphire/Emerald
        if theme == "dark":
            return ThemePalette(
                frame_dark=(16, 24, 32),
                frame_mid=(48, 64, 80),
                panel_bg=(32, 48, 64),
                panel_bg_dark=(24, 32, 48),
                text_dark=(240, 248, 255),
                text_mid=(160, 192, 224),
                text_light=(96, 128, 160),
                header_bg=(16, 24, 32),
                header_text=(240, 248, 255),
                font_hint="sans"
            )
        else:
            return ThemePalette(
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
            )
    elif gen == 4:
        # Gen 4: DS Diamond/Pearl/Platinum
        if theme == "dark":
            return ThemePalette(
                frame_dark=(24, 24, 24),
                frame_mid=(64, 64, 64),
                panel_bg=(48, 48, 48),
                panel_bg_dark=(32, 32, 32),
                text_dark=(248, 248, 248),
                text_mid=(200, 200, 200),
                text_light=(120, 120, 120),
                header_bg=(24, 24, 24),
                header_text=(248, 248, 248),
                font_hint="sans"
            )
        else:
            return ThemePalette(
                frame_dark=(48, 48, 48),
                frame_mid=(128, 128, 128),
                panel_bg=(248, 248, 248),
                panel_bg_dark=(224, 224, 224),
                text_dark=(32, 32, 32),
                text_mid=(88, 88, 88),
                text_light=(160, 160, 160),
                header_bg=(48, 48, 48),
                header_text=(255, 255, 255),
                font_hint="sans"
            )
    elif gen == 5:
        # Gen 5: DS Black/White (This is the original default style)
        if theme == "dark":
            return ThemePalette(
                frame_dark=(16, 16, 16),
                frame_mid=(48, 48, 48),
                panel_bg=(32, 32, 32),
                panel_bg_dark=(24, 24, 24),
                text_dark=(255, 255, 255),
                text_mid=(180, 180, 180),
                text_light=(100, 100, 100),
                header_bg=(16, 16, 16),
                header_text=(255, 255, 255),
                font_hint="sans"
            )
        else:
            return ThemePalette(
                frame_dark=(40, 48, 72),
                frame_mid=(72, 80, 112),
                panel_bg=(248, 248, 240),
                panel_bg_dark=(232, 232, 216),
                text_dark=(40, 40, 40),
                text_mid=(88, 88, 88),
                text_light=(136, 136, 136),
                header_bg=(48, 56, 112),
                header_text=(255, 255, 255),
                font_hint="sans"
            )
    else:
        # Gen 6-9: Modern 3D Era (Clean, flat UI)
        if theme == "dark":
            return ThemePalette(
                frame_dark=(20, 20, 20),
                frame_mid=(60, 60, 60),
                panel_bg=(40, 40, 40),
                panel_bg_dark=(30, 30, 30),
                text_dark=(250, 250, 250),
                text_mid=(200, 200, 200),
                text_light=(150, 150, 150),
                header_bg=(220, 40, 40), # Modern Rotom Dex / Switch Red
                header_text=(255, 255, 255),
                font_hint="sans"
            )
        else:
            return ThemePalette(
                frame_dark=(200, 200, 200),
                frame_mid=(230, 230, 230),
                panel_bg=(255, 255, 255),
                panel_bg_dark=(245, 245, 245),
                text_dark=(20, 20, 20),
                text_mid=(100, 100, 100),
                text_light=(180, 180, 180),
                header_bg=(230, 50, 50), # Modern Rotom Dex / Switch Red
                header_text=(255, 255, 255),
                font_hint="sans"
            )

DEFAULT_PALETTE = get_palette(5, "light")
