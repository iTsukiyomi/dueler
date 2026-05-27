import re

def main():
    filepath = "pokemonduel/canvas/renderer.py"
    with open(filepath, "r") as f:
        content = f.read()

    # 1. Remove the global color palette definitions
    start_idx = content.find("# ── Classic Pokémon UI Color Palette ──")
    end_idx = content.find("class BattleRenderer:")
    
    if start_idx != -1 and end_idx != -1:
        replacement = "from .themes import DEFAULT_PALETTE, ThemePalette\n\n\n"
        content = content[:start_idx] + replacement + content[end_idx:]

    # 2. Modify __init__ to accept palette
    content = content.replace(
        "def __init__(self, data_dir: Path) -> None:",
        "def __init__(self, data_dir: Path, palette: ThemePalette = DEFAULT_PALETTE) -> None:\n        self.palette = palette"
    )

    # 3. Replace default args in method signatures
    content = content.replace("fill=_PANEL_BG", "fill=None")
    content = content.replace("border=_FRAME_DARK", "border=None")
    content = content.replace("bg=_HEADER_BG", "bg=None")

    # Inject defaults inside methods
    # _draw_classic_panel
    panel_find = "def _draw_classic_panel(self, draw: ImageDraw.ImageDraw,\n                            x1: float, y1: float, x2: float, y2: float,\n                            *, fill=None, border=None, border_width: int = 2,\n                            radius: int = 4) -> None:\n        \"\"\"Draw a classic Pokémon-style bordered panel (solid fill, dark border).\"\"\""
    panel_replace = panel_find + "\n        fill = fill or self.palette.panel_bg\n        border = border or self.palette.frame_dark"
    content = content.replace(panel_find, panel_replace)

    # _draw_header_bar
    header_find = "def _draw_header_bar(self, draw: ImageDraw.ImageDraw,\n                         x1: float, y1: float, x2: float, height: int = 24,\n                         text: str = \"\", *, bg=None) -> None:\n        \"\"\"Draw a classic dark header bar with white text (Gen 3/5 style).\"\"\""
    header_replace = header_find + "\n        bg = bg or self.palette.header_bg"
    content = content.replace(header_find, header_replace)

    # 4. Global replacements
    replacements = {
        "_FRAME_DARK": "self.palette.frame_dark",
        "_FRAME_MID": "self.palette.frame_mid",
        "_PANEL_BG_DARK": "self.palette.panel_bg_dark",
        "_PANEL_BG": "self.palette.panel_bg",
        "_TEXT_DARK": "self.palette.text_dark",
        "_TEXT_MID": "self.palette.text_mid",
        "_TEXT_LIGHT": "self.palette.text_light",
        "_HEADER_BG": "self.palette.header_bg",
        "_HEADER_TEXT": "self.palette.header_text",
        "_HP_GREEN": "self.palette.hp_green",
        "_HP_YELLOW": "self.palette.hp_yellow",
        "_HP_RED": "self.palette.hp_red",
        "_HP_BG": "self.palette.hp_bg",
        "_HP_BORDER": "self.palette.hp_border",
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)

    # 5. Handle font logic based on self.palette.font_hint
    # we can append a custom font loader logic if needed later

    with open(filepath, "w") as f:
        f.write(content)
        
    print("Successfully patched renderer.py")

if __name__ == "__main__":
    main()
