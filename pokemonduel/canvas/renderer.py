import io
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from .assets import AssetLoader

# ── Classic Pokémon Type Colors (Gen 3/5 palette) ──
TYPE_COLORS = {
    "normal":   (168, 168, 120, 255),
    "fire":     (240, 128, 48, 255),
    "water":    (104, 144, 240, 255),
    "electric": (248, 208, 48, 255),
    "grass":    (120, 200, 80, 255),
    "ice":      (152, 216, 216, 255),
    "fighting": (192, 48, 40, 255),
    "poison":   (160, 64, 160, 255),
    "ground":   (224, 192, 104, 255),
    "flying":   (168, 144, 240, 255),
    "psychic":  (248, 88, 136, 255),
    "bug":      (168, 184, 32, 255),
    "rock":     (184, 160, 56, 255),
    "ghost":    (112, 88, 152, 255),
    "dragon":   (112, 56, 248, 255),
    "dark":     (112, 88, 72, 255),
    "steel":    (184, 184, 208, 255),
    "fairy":    (238, 153, 172, 255),
    "stellar":  (74, 186, 176, 255),
    "unknown":  (104, 160, 144, 255),
}

STATUS_COLORS = {
    "burn":     (240, 128, 48, 255),
    "brn":      (240, 128, 48, 255),
    "poison":   (160, 64, 160, 255),
    "psn":      (160, 64, 160, 255),
    "tox":      (130, 40, 200, 255),
    "b-poison": (130, 40, 200, 255),
    "paralysis":(248, 208, 48, 255),
    "par":      (248, 208, 48, 255),
    "sleep":    (104, 144, 240, 255),
    "slp":      (104, 144, 240, 255),
    "freeze":   (152, 216, 216, 255),
    "frz":      (152, 216, 216, 255),
}

# Type ID → Name mapping
_TYPE_ID_TO_NAME = {
    1: "Normal", 2: "Fighting", 3: "Flying", 4: "Poison", 5: "Ground",
    6: "Rock", 7: "Bug", 8: "Ghost", 9: "Steel", 10: "Fire",
    11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
    16: "Dragon", 17: "Dark", 18: "Fairy",
}

# ── Classic Pokémon UI Color Palette ──
_FRAME_DARK    = (40, 48, 72)       # Dark blue-grey frame border
_FRAME_MID     = (72, 80, 112)      # Medium frame accent
_PANEL_BG      = (248, 248, 240)    # Off-white panel fill
_PANEL_BG_DARK = (232, 232, 216)    # Slightly darker panel
_TEXT_DARK     = (40, 40, 40)       # Primary text color
_TEXT_MID      = (88, 88, 88)       # Secondary text
_TEXT_LIGHT    = (136, 136, 136)    # Tertiary text
_HEADER_BG     = (48, 56, 112)     # Dark blue header bar
_HEADER_TEXT   = (255, 255, 255)   # White header text
_HP_GREEN      = (80, 200, 72)     # HP bar green
_HP_YELLOW     = (248, 200, 48)    # HP bar yellow
_HP_RED        = (240, 72, 56)     # HP bar red
_HP_BG         = (56, 56, 56)      # HP bar background
_HP_BORDER     = (40, 40, 40)      # HP bar border


class BattleRenderer:
    """Classic Pokémon-style canvas rendering pipeline for battle screens, teams, and profiles."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sprite_dir = data_dir / "img"
        self.asset_loader = AssetLoader(data_dir / "canvas_assets")
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> dict[str, ImageFont.ImageFont]:
        """Load fonts, preferring clean sans-serif for classic game feel."""
        font_paths = [
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        ]

        bold_path = None
        reg_path = None
        for p in font_paths:
            if Path(p).exists():
                if "Bold" in p and not bold_path:
                    bold_path = p
                elif not reg_path:
                    reg_path = p

        if not bold_path:
            bold_path = reg_path

        fonts = {}
        try:
            fonts["title"]      = ImageFont.truetype(bold_path or "arial.ttf", 20)
            fonts["body"]       = ImageFont.truetype(reg_path or "arial.ttf", 14)
            fonts["body_bold"]  = ImageFont.truetype(bold_path or "arial.ttf", 14)
            fonts["small"]      = ImageFont.truetype(reg_path or "arial.ttf", 11)
            fonts["small_bold"] = ImageFont.truetype(bold_path or "arial.ttf", 11)
            fonts["tiny"]       = ImageFont.truetype(reg_path or "arial.ttf", 9)
            fonts["hp_label"]   = ImageFont.truetype(bold_path or "arial.ttf", 10)
        except Exception:
            default = ImageFont.load_default()
            for key in ("title", "body", "body_bold", "small", "small_bold", "tiny", "hp_label"):
                # pyrefly: ignore [unsupported-operation]
                fonts[key] = default

        # pyrefly: ignore [bad-return]
        return fonts

    def _load_sprite(self, poke_id: Optional[int], size: Tuple[int, int]) -> Optional[Image.Image]:
        """Safely loads and scales a Pokémon sprite from disk."""
        if poke_id is None:
            return None
        for ext in ("png", "gif", "jpg"):
            path = self.sprite_dir / f"{poke_id}.{ext}"
            if path.exists():
                try:
                    img = Image.open(path).convert("RGBA")
                    if getattr(img, "is_animated", False):
                        img.seek(0)
                        img = img.convert("RGBA")
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    return img
                except Exception:
                    continue
        return None

    # ── Classic UI Drawing Primitives ──

    def _draw_classic_panel(self, draw: ImageDraw.ImageDraw,
                            x1: float, y1: float, x2: float, y2: float,
                            *, fill=_PANEL_BG, border=_FRAME_DARK, border_width: int = 2,
                            radius: int = 4) -> None:
        """Draw a classic Pokémon-style bordered panel (solid fill, dark border)."""
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(*fill, 255) if len(fill) == 3 else fill)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=(*border, 255) if len(border) == 3 else border, width=border_width)

    def _draw_header_bar(self, draw: ImageDraw.ImageDraw,
                         x1: float, y1: float, x2: float, height: int = 24,
                         text: str = "", *, bg=_HEADER_BG) -> None:
        """Draw a classic dark header bar with white text (Gen 3/5 style)."""
        draw.rounded_rectangle([x1, y1, x2, y1 + height], radius=4, fill=(*bg, 255) if len(bg) == 3 else bg)
        if text:
            font = self.fonts["body_bold"]
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = x1 + ((x2 - x1) - (bbox[2] - bbox[0])) // 2
            ty = y1 + (height - (bbox[3] - bbox[1])) // 2 - 1
            draw.text((tx, ty), text, fill=_HEADER_TEXT, font=font)

    def _draw_type_badge(self, draw: ImageDraw.ImageDraw,
                         x: float, y: float, type_name: str,
                         *, width: int = 60, height: int = 18) -> Tuple[float, float]:
        """Draw a classic Gen 3/5 style type rectangle badge."""
        color = TYPE_COLORS.get(type_name.lower(), (128, 128, 128, 255))
        font = self.fonts["small_bold"]

        # Filled rounded rectangle with slight darker border
        draw.rounded_rectangle([x, y, x + width, y + height], radius=3,
                               fill=color, outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40), 255), width=1)

        # Centered white text
        label = type_name.upper()
        bbox = draw.textbbox((0, 0), label, font=font)
        tx = x + (width - (bbox[2] - bbox[0])) // 2
        ty = y + (height - (bbox[3] - bbox[1])) // 2 - 1

        # Text shadow for readability
        draw.text((tx + 1, ty + 1), label, fill=(0, 0, 0, 100), font=font)
        draw.text((tx, ty), label, fill=(255, 255, 255, 255), font=font)

        return width, height

    def _draw_status_badge(self, draw: ImageDraw.ImageDraw,
                           x: float, y: float, status: str) -> Tuple[float, float]:
        """Draw a classic Gen 5 style status label (BRN, PAR, etc.)."""
        status_clean = status.lower().strip()
        badge_text = status_clean[:3].upper()
        color = STATUS_COLORS.get(status_clean, (128, 128, 128, 255))

        font = self.fonts["small_bold"]
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_w = bbox[2] - bbox[0]
        w = text_w + 10
        h = 16

        # Solid rectangle with darker border
        draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=color,
                               outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40), 255), width=1)
        draw.text((x + 5, y + (h - (bbox[3] - bbox[1])) // 2 - 1), badge_text,
                  fill=(255, 255, 255, 255), font=font)

        return w, h

    def _draw_hp_bar(self, draw: ImageDraw.ImageDraw,
                     x: float, y: float, w: float, h: float,
                     current: int, maximum: int) -> None:
        """Classic thin Pokémon HP bar (green→yellow→red, dark border)."""
        ratio = max(0.0, min(1.0, current / maximum if maximum > 0 else 0.0))

        # "HP:" label on the left
        font = self.fonts["hp_label"]
        draw.text((x - 24, y - 1), "HP:", fill=_TEXT_DARK, font=font)

        # Background bar with dark border
        draw.rounded_rectangle([x, y, x + w, y + h], radius=2, fill=_HP_BG)

        if ratio > 0.0:
            fill_w = max(3, int(w * ratio))
            if ratio > 0.5:
                color = _HP_GREEN
            elif ratio > 0.2:
                color = _HP_YELLOW
            else:
                color = _HP_RED
            draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=2, fill=color)

        # Thin border
        draw.rounded_rectangle([x, y, x + w, y + h], radius=2, outline=_HP_BORDER, width=1)

        # HP text to the right
        hp_text = f"{current}/{maximum}"
        hp_font = self.fonts["small"]
        draw.text((x + w + 6, y - 2), hp_text, fill=_TEXT_DARK, font=hp_font)

    def _draw_hud(self, draw: ImageDraw.ImageDraw,
                  x: float, y: float, poke, is_left: bool) -> None:
        """Classic Gen 3/5 HUD card for an active Pokémon."""
        width = 310
        height = 80

        # Classic solid panel (cream/white with dark border)
        self._draw_classic_panel(draw, x, y, x + width, y + height,
                                 fill=_PANEL_BG, border=_FRAME_DARK)

        # Name
        name_text = poke._name.replace('-', ' ').title()
        nick_text = getattr(poke, '_nickname', None)
        display_name = nick_text if nick_text and nick_text != "None" else name_text

        font_name = self.fonts["body_bold"]
        draw.text((x + 10, y + 8), display_name, fill=_TEXT_DARK, font=font_name)

        # Level (right-aligned)
        level = getattr(poke, 'level', 100)
        level_text = f"Lv{level}"
        font_small = self.fonts["body"]
        lv_bbox = draw.textbbox((0, 0), level_text, font=font_small)
        lv_x = x + width - (lv_bbox[2] - lv_bbox[0]) - 10
        draw.text((lv_x, y + 8), level_text, fill=_TEXT_MID, font=font_small)

        # Gender icon
        gender = getattr(poke, 'gender', '')
        if gender == '-m':
            draw.text((lv_x - 16, y + 8), "♂", fill=(80, 128, 240, 255), font=font_small)
        elif gender == '-f':
            draw.text((lv_x - 16, y + 8), "♀", fill=(240, 104, 128, 255), font=font_small)

        # HP Bar
        max_hp = poke.starting_hp
        current_hp = max(0, poke.hp)
        self._draw_hp_bar(draw, x + 38, y + 36, width - 110, 8, current_hp, max_hp)

        # Status badge
        curr_y = y + 54
        start_x = x + 10
        if poke.nv.current:
            badge_w, _ = self._draw_status_badge(draw, start_x, curr_y, poke.nv.current)
            start_x += badge_w + 6

        # Stat stages (compact)
        stages = getattr(poke, 'stages', {})
        if stages:
            stage_parts = []
            for stat, val in stages.items():
                if val != 0:
                    sign = "+" if val > 0 else ""
                    arrow = "↑" if val > 0 else "↓"
                    stage_parts.append(f"{stat.upper()}{sign}{val}{arrow}")
            if stage_parts:
                stages_text = " ".join(stage_parts[:3])
                draw.text((start_x, curr_y + 1), stages_text, fill=_TEXT_MID, font=self.fonts["small"])

    def _draw_terrain_overlay(self, draw: ImageDraw.ImageDraw, terrain: str, width: int, height: int) -> None:
        """Draw subtle terrain indicators on the battlefield."""
        terrain_low = terrain.lower().strip()
        if terrain_low in ("normal", "clear", "none"):
            return

        horizon_y = int(height * 0.45)

        if "electric" in terrain_low:
            color = (248, 208, 48, 50)
            for y in range(horizon_y, height, 12):
                draw.line([(0, y), (width, y)], fill=color, width=1)
        elif "grassy" in terrain_low:
            color = (80, 184, 48, 50)
            for y in range(horizon_y, height, 10):
                draw.line([(0, y), (width, y)], fill=color, width=2)
        elif "misty" in terrain_low:
            for y in range(height - 80, height, 5):
                opacity = int(30 * ((y - (height - 80)) / 80))
                draw.line([(0, y), (width, y)], fill=(248, 200, 248, opacity), width=3)
        elif "psychic" in terrain_low:
            color = (248, 88, 136, 40)
            for y in range(horizon_y, height, 14):
                draw.line([(0, y), (width, y)], fill=color, width=1)

    def _apply_weather_overlay(self, canvas: Image.Image, weather: str) -> None:
        """Apply weather effects with classic styling (not too heavy)."""
        weather_low = weather.lower().strip()
        if weather_low in ("clear", "none", ""):
            return

        width, height = canvas.size
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        import random
        rnd = random.Random(42)

        if "sun" in weather_low or "sunny" in weather_low:
            # Warm golden tint
            draw.rectangle([0, 0, width, height], fill=(255, 200, 80, 18))

        elif "rain" in weather_low:
            # Blue tint + rain streaks
            draw.rectangle([0, 0, width, height], fill=(40, 80, 160, 18))
            for _ in range(60):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(12, 25)
                draw.line([(rx, ry), (rx - 4, ry + length)], fill=(160, 200, 240, 120), width=1)

        elif "sandstorm" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(200, 176, 120, 30))
            for _ in range(80):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(8, 18)
                draw.line([(rx, ry), (rx + length, ry + 2)], fill=(176, 152, 96, 80), width=1)

        elif "hail" in weather_low or "snow" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(200, 230, 255, 15))
            for _ in range(40):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                r = rnd.randint(1, 3)
                draw.ellipse([rx-r, ry-r, rx+r, ry+r], fill=(255, 255, 255, 160))

        canvas.alpha_composite(overlay)

    # ── Main Rendering Methods ──

    def render_battle_screen(self, battle) -> io.BytesIO:
        """Generates a classic Pokémon-style battle screen image."""
        width, height = 960, 540

        weather = getattr(battle.weather, "_weather_type", "clear") or "clear"
        terrain = getattr(battle.terrain, "item", "normal") or "normal"
        trick_room_active = False
        if hasattr(battle, "trick_room") and battle.trick_room.active():
            trick_room_active = True

        bg_name = "trick_room" if trick_room_active else "stadium_classic"
        canvas = self.asset_loader.get_background(bg_name, width, height).copy()
        draw = ImageDraw.Draw(canvas)

        horizon_y = int(height * 0.45)

        # Classic battle platforms (flat elliptical ground markers)
        # Left platform (player side — bottom-left area)
        plat_left_cx, plat_left_cy = 230, 400
        draw.ellipse([plat_left_cx - 120, plat_left_cy - 20, plat_left_cx + 120, plat_left_cy + 20],
                     fill=(96, 160, 56, 80), outline=(56, 120, 40, 180), width=2)

        # Right platform (opponent side — upper-right area)
        plat_right_cx, plat_right_cy = 730, 380
        draw.ellipse([plat_right_cx - 110, plat_right_cy - 18, plat_right_cx + 110, plat_right_cy + 18],
                     fill=(96, 160, 56, 80), outline=(56, 120, 40, 180), width=2)

        # Terrain overlays
        self._draw_terrain_overlay(draw, terrain, width, height)

        # Active Pokémon Sprites
        t1_poke = battle.trainer1.current_pokemon
        t2_poke = battle.trainer2.current_pokemon

        t1_id = getattr(t1_poke, 'pokemon_id', getattr(t1_poke, 'id', None))
        t2_id = getattr(t2_poke, 'pokemon_id', getattr(t2_poke, 'id', None))

        sprite_w, sprite_h = 200, 200

        # Left Pokémon (player's — larger, lower on screen)
        sprite_left = self._load_sprite(t1_id, (sprite_w, sprite_h))
        if sprite_left:
            canvas.paste(sprite_left, (130, 230), sprite_left)
        else:
            draw.rectangle([170, 260, 290, 380], fill=(80, 140, 60, 60), outline=(56, 120, 40, 160))
            draw.text((215, 310), "?", fill=_TEXT_MID, font=self.fonts["title"])

        # Right Pokémon (opponent's — slightly smaller, higher)
        sprite_right = self._load_sprite(t2_id, (sprite_w - 10, sprite_h - 10))
        if sprite_right:
            sprite_right = sprite_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            canvas.paste(sprite_right, (635, 210), sprite_right)
        else:
            draw.rectangle([670, 250, 790, 370], fill=(80, 140, 60, 60), outline=(56, 120, 40, 160))
            draw.text((715, 300), "?", fill=_TEXT_MID, font=self.fonts["title"])

        # Weather overlay
        self._apply_weather_overlay(canvas, weather)

        # HUD Cards (classic solid panels)
        # Right-side HUD for opponent (upper right)
        self._draw_hud(draw, 560, 30, t2_poke, is_left=False)
        # Left-side HUD for player (lower left)
        self._draw_hud(draw, 50, 440, t1_poke, is_left=True)

        # Center info panel (Turn / Weather / Terrain)
        info_w, info_h = 160, 60
        info_x = (width - info_w) // 2
        info_y = 16
        self._draw_classic_panel(draw, info_x, info_y, info_x + info_w, info_y + info_h,
                                 fill=_PANEL_BG, border=_FRAME_DARK)

        turn = getattr(battle, 'turn', 1)
        turn_text = f"TURN {turn}"
        tb = draw.textbbox((0, 0), turn_text, font=self.fonts["body_bold"])
        draw.text((info_x + (info_w - (tb[2] - tb[0])) // 2, info_y + 6),
                  turn_text, fill=_TEXT_DARK, font=self.fonts["body_bold"])

        # Weather/terrain subtitles
        if weather != "clear":
            w_text = weather.replace("-", " ").title()
            w_tb = draw.textbbox((0, 0), w_text, font=self.fonts["small"])
            draw.text((info_x + (info_w - (w_tb[2] - w_tb[0])) // 2, info_y + 26),
                      w_text, fill=(200, 120, 40), font=self.fonts["small"])

        if terrain not in ("normal", "none", "clear"):
            t_text = terrain.replace("-", " ").title()
            t_tb = draw.textbbox((0, 0), t_text, font=self.fonts["small"])
            draw.text((info_x + (info_w - (t_tb[2] - t_tb[0])) // 2, info_y + 42),
                      t_text, fill=(80, 160, 56), font=self.fonts["small"])

        # Outer frame border (classic game window)
        draw.rectangle([0, 0, width - 1, height - 1], outline=_FRAME_DARK, width=3)
        draw.rectangle([3, 3, width - 4, height - 4], outline=_FRAME_MID, width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_team_preview(self, battle) -> io.BytesIO:
        """Generates a classic Pokémon-style team preview screen."""
        width, height = 760, 380
        canvas = self.asset_loader.get_background("team_preview_bg", width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # Classic header bar
        self._draw_header_bar(draw, 20, 10, width - 20, 28,
                              text=f"TEAM PREVIEW — {battle.trainer1.name} vs {battle.trainer2.name}")

        poke_w, poke_h = 84, 84
        col_gap = 14
        row1_y = 60
        row2_y = 220

        def draw_team_row(trainer, start_y, label_text):
            party = trainer.party[:6]
            row_width = len(party) * poke_w + (len(party) - 1) * col_gap
            start_x = (width - row_width) // 2

            # Trainer label
            draw.text((start_x, start_y - 18), label_text,
                      fill=_HEADER_TEXT, font=self.fonts["small_bold"])

            for idx, poke in enumerate(party):
                px = start_x + idx * (poke_w + col_gap)

                # Classic bordered pocket
                self._draw_classic_panel(draw, px, start_y, px + poke_w, start_y + poke_h,
                                         fill=(40, 56, 96), border=(72, 88, 136), border_width=2)

                poke_id = getattr(poke, 'pokemon_id', getattr(poke, 'id', None))
                sprite = self._load_sprite(poke_id, (76, 76))
                if sprite:
                    canvas.paste(sprite, (int(px + 4), int(start_y + 4)), sprite)
                else:
                    draw.text((px + 34, start_y + 30), "?", fill=(160, 168, 200, 200), font=self.fonts["title"])

                # Name below pocket
                name = poke._name.replace('-', ' ').title()
                if len(name) > 10:
                    name = name[:8] + ".."
                name_font = self.fonts["small"]
                nb = draw.textbbox((0, 0), name, font=name_font)
                nx = px + (poke_w - (nb[2] - nb[0])) // 2
                draw.text((nx, start_y + poke_h + 4), name, fill=_HEADER_TEXT, font=name_font)

                # Mini HP indicator
                hp_text = f"{poke.hp}hp"
                hp_font = self.fonts["tiny"]
                hb = draw.textbbox((0, 0), hp_text, font=hp_font)
                hx = px + (poke_w - (hb[2] - hb[0])) // 2
                draw.text((hx, start_y + poke_h + 18), hp_text, fill=(160, 200, 160), font=hp_font)

        draw_team_row(battle.trainer1, row1_y, f"▸ {battle.trainer1.name}'s Party:")
        draw_team_row(battle.trainer2, row2_y, f"▸ {battle.trainer2.name}'s Party:")

        # Divider line between teams
        div_y = (row1_y + poke_h + 36 + row2_y - 18) // 2
        draw.line([(40, div_y), (width - 40, div_y)], fill=(72, 88, 136, 180), width=1)

        # Outer frame
        draw.rectangle([0, 0, width - 1, height - 1], outline=_FRAME_DARK, width=2)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def _get_base_stats(self, identifier: str) -> dict[str, int]:
        """Look up base stats from static registries. Fixed to use proper registry API."""
        try:
            from ..core.registry import FORMS, POKEMON_STATS
            # Use the correct .get() API on the registry
            form = FORMS.get(identifier.lower())
            if form:
                pid = form.get("pokemon_id") or form.get("id")
                if pid is not None:
                    stats_rec = POKEMON_STATS.find_one({"pokemon_id": pid})
                    if stats_rec and "stats" in stats_rec:
                        stats = stats_rec["stats"]
                        return {
                            "hp":  stats[0] if len(stats) > 0 else 50,
                            "atk": stats[1] if len(stats) > 1 else 50,
                            "def": stats[2] if len(stats) > 2 else 50,
                            "spa": stats[3] if len(stats) > 3 else 50,
                            "spd": stats[4] if len(stats) > 4 else 50,
                            "spe": stats[5] if len(stats) > 5 else 50,
                        }
        except Exception:
            pass
        return {"hp": 50, "atk": 50, "def": 50, "spa": 50, "spd": 50, "spe": 50}

    def _get_type_names(self, identifier: str) -> list[str]:
        """Look up Pokémon type names from the PTYPES registry."""
        try:
            from ..core.registry import FORMS, PTYPES
            form = FORMS.get(identifier.lower())
            if form:
                pid = form.get("pokemon_id")
                if pid is not None:
                    ptype_entry = PTYPES.get(pid)
                    if ptype_entry and "types" in ptype_entry:
                        return [_TYPE_ID_TO_NAME.get(tid, "???") for tid in ptype_entry["types"]]
        except Exception:
            pass
        return []

    def render_pokemon_card(self, poke, player_name: str = "Trainer", type_names: list[str] | None = None) -> io.BytesIO:
        """Generates a classic Pokémon summary screen-style card."""
        width, height = 500, 310
        canvas = self.asset_loader.get_background("card_bg", width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # Extract values depending on whether input is dict or object
        from ..core.registry import FORMS, POKE_ABILITIES, ABILITIES
        if isinstance(poke, dict):
            pokname = poke.get("pokname", "")
            poke_id = None
            if pokname:
                form_info = FORMS.get(pokname.lower())
                if form_info:
                    poke_id = form_info.get("pokemon_id")
            if not poke_id:
                poke_id = poke.get("pokid", poke.get("pokemon_id", poke.get("id", None)))

            name_text = poke.get("pokname", "?").replace('-', ' ').title()
            nick_text = poke.get("nickname") or poke.get("_nickname")
            display_name = nick_text if nick_text and nick_text != "None" else name_text

            nature_val = poke.get("nature", "Serious")

            # Resolve ability dynamically
            ability_val = poke.get("ability", "None")
            if (ability_val == "None" or not ability_val) and "ability_index" in poke:
                pn = poke.get("pokname", "").lower()
                form_info = FORMS.get(pn)
                if form_info:
                    pokemon_id = form_info["pokemon_id"]
                    records = POKE_ABILITIES.by_secondary(pokemon_id)
                    curr_idx = poke.get("ability_index", 0)
                    if records and 0 <= curr_idx < len(records):
                        ab_id = records[curr_idx]["ability_id"]
                        ab_data = ABILITIES.find_one({"id": ab_id})
                        if ab_data:
                            ability_val = ab_data.get("identifier", "None")

            item_val = poke.get("hitem", "None")
            base_stats = self._get_base_stats(poke.get("pokname", ""))

            # Resolve types if not passed
            if type_names is None:
                type_names = self._get_type_names(poke.get("pokname", ""))

            ivs = {
                "hp": poke.get("hpiv", 31), "atk": poke.get("atkiv", 31),
                "def": poke.get("defiv", 31), "spa": poke.get("spatkiv", 31),
                "spd": poke.get("spdefiv", 31), "spe": poke.get("speediv", 31)
            }
            evs = {
                "hp": poke.get("hpev", 0), "atk": poke.get("atkev", 0),
                "def": poke.get("defev", 0), "spa": poke.get("spatkev", 0),
                "spd": poke.get("spdefev", 0), "spe": poke.get("speedev", 0)
            }
            moves = poke.get("moves", [])
        else:
            raw_name = getattr(poke, '_name', '').lower()
            poke_id = None
            if raw_name:
                form_info = FORMS.get(raw_name)
                if form_info:
                    poke_id = form_info.get("pokemon_id")
            if not poke_id:
                poke_id = getattr(poke, 'pokemon_id', getattr(poke, 'id', None))

            name_text = getattr(poke, '_name', '').replace('-', ' ').title()
            nick_text = getattr(poke, '_nickname', None)
            display_name = nick_text if nick_text and nick_text != "None" else name_text

            nature_val = getattr(poke, 'nature', 'Serious')

            ability_val = getattr(poke, 'ability', 'None')
            if (ability_val == "None" or not ability_val) and hasattr(poke, "ability_index"):
                pn = getattr(poke, '_name', "").lower()
                form_info = FORMS.get(pn)
                if form_info:
                    pokemon_id = form_info["pokemon_id"]
                    records = POKE_ABILITIES.by_secondary(pokemon_id)
                    curr_idx = getattr(poke, "ability_index", 0)
                    if records and 0 <= curr_idx < len(records):
                        ab_id = records[curr_idx]["ability_id"]
                        ab_data = ABILITIES.find_one({"id": ab_id})
                        if ab_data:
                            ability_val = ab_data.get("identifier", "None")

            item_val = getattr(poke, 'item', 'None')

            # Base stats from object
            bs = getattr(poke, 'base_stats', {})
            raw_name_obj = getattr(poke, '_name', '').lower()
            if raw_name_obj in bs:
                bs_raw = bs[raw_name_obj]
            elif name_text.lower() in bs:
                bs_raw = bs[name_text.lower()]
            else:
                bs_raw = bs
            if isinstance(bs_raw, list):
                base_stats = {
                    "hp": bs_raw[0] if len(bs_raw) > 0 else 50,
                    "atk": bs_raw[1] if len(bs_raw) > 1 else 50,
                    "def": bs_raw[2] if len(bs_raw) > 2 else 50,
                    "spa": bs_raw[3] if len(bs_raw) > 3 else 50,
                    "spd": bs_raw[4] if len(bs_raw) > 4 else 50,
                    "spe": bs_raw[5] if len(bs_raw) > 5 else 50,
                }
            elif isinstance(bs_raw, dict):
                base_stats = bs_raw
            else:
                base_stats = self._get_base_stats(getattr(poke, '_name', ''))

            # Resolve types
            if type_names is None:
                type_names = self._get_type_names(getattr(poke, '_name', ''))

            ivs = {
                "hp": getattr(poke, "hpiv", 31), "atk": getattr(poke, "atkiv", 31),
                "def": getattr(poke, "defiv", 31), "spa": getattr(poke, "spatkiv", 31),
                "spd": getattr(poke, "spdefiv", 31), "spe": getattr(poke, "speediv", 31)
            }
            evs = {
                "hp": getattr(poke, "hpev", 0), "atk": getattr(poke, "atkev", 0),
                "def": getattr(poke, "defev", 0), "spa": getattr(poke, "spatkev", 0),
                "spd": getattr(poke, "spdefev", 0), "spe": getattr(poke, "speedev", 0)
            }
            moves = getattr(poke, 'moves', [])

        # ── Layout: Classic Pokémon Summary Screen ──

        # Header bar with Pokémon name
        self._draw_header_bar(draw, 4, 8, width - 4, 26, text=display_name, bg=_HEADER_BG)

        # Type badges (right of header or below)
        if type_names:
            badge_x = width - 10
            for tn in reversed(type_names):
                bw = 58
                badge_x -= bw + 4
                self._draw_type_badge(draw, badge_x, 10, tn, width=bw, height=22)

        # Sprite panel (left side)
        sprite_panel_x, sprite_panel_y = 14, 44
        sprite_panel_w, sprite_panel_h = 150, 150
        self._draw_classic_panel(draw, sprite_panel_x, sprite_panel_y,
                                 sprite_panel_x + sprite_panel_w, sprite_panel_y + sprite_panel_h,
                                 fill=(232, 232, 224), border=_FRAME_DARK)

        sprite = self._load_sprite(poke_id, (140, 140))
        if sprite:
            canvas.paste(sprite, (sprite_panel_x + 5, sprite_panel_y + 5), sprite)
        else:
            draw.text((sprite_panel_x + 65, sprite_panel_y + 65), "?",
                      fill=_TEXT_LIGHT, font=self.fonts["title"])

        # Info section (right of sprite)
        info_x = sprite_panel_x + sprite_panel_w + 12
        info_y = 48

        if not item_val or item_val == "None":
            item_val = "None"

        info_lines = [
            ("Nature:", str(nature_val).title()),
            ("Ability:", str(ability_val).replace('-', ' ').title()),
            ("Item:", str(item_val).replace('-', ' ').title()),
        ]

        for i, (label, value) in enumerate(info_lines):
            ly = info_y + i * 20
            draw.text((info_x, ly), label, fill=_TEXT_MID, font=self.fonts["small_bold"])
            draw.text((info_x + 52, ly), value, fill=_TEXT_DARK, font=self.fonts["small"])

        # ── Stats Table (below info, classic grid) ──
        stats_y = info_y + 68
        stat_header = "STAT   BASE   IV   EV"
        draw.text((info_x, stats_y), stat_header, fill=_HEADER_BG, font=self.fonts["small_bold"])

        # Horizontal rule under header
        draw.line([(info_x, stats_y + 14), (width - 16, stats_y + 14)], fill=_FRAME_MID, width=1)

        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP ", "ATK", "DEF", "SPA", "SPD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + 18 + (idx * 15)
            lbl = stats_labels[idx]

            bs_v = base_stats.get(key, 0)
            iv_v = ivs.get(key, 31)
            ev_v = evs.get(key, 0)

            # Label with slightly different color per stat
            draw.text((info_x, y_offset), f"{lbl:<5}", fill=_TEXT_DARK, font=self.fonts["small_bold"])
            draw.text((info_x + 48, y_offset), f"{bs_v:<5}", fill=_TEXT_DARK, font=self.fonts["small"])
            draw.text((info_x + 100, y_offset), f"{iv_v:<4}", fill=(80, 120, 200), font=self.fonts["small"])
            draw.text((info_x + 140, y_offset), f"{ev_v:<4}", fill=(200, 120, 60), font=self.fonts["small"])

        # ── Moveset section (bottom-left, below sprite) ──
        moves_y = sprite_panel_y + sprite_panel_h + 10
        self._draw_classic_panel(draw, 14, moves_y, sprite_panel_x + sprite_panel_w, height - 10,
                                 fill=(240, 240, 232), border=_FRAME_MID, border_width=1)

        draw.text((20, moves_y + 4), "MOVES", fill=_HEADER_BG, font=self.fonts["small_bold"])
        draw.line([(20, moves_y + 18), (sprite_panel_x + sprite_panel_w - 6, moves_y + 18)],
                  fill=_FRAME_MID, width=1)

        for idx, move in enumerate(moves[:4]):
            m_y = moves_y + 22 + (idx * 14)
            if isinstance(move, str):
                m_name = move.replace('-', ' ').title()
            else:
                m_name = getattr(move, 'pretty_name', str(move))
            draw.text((24, m_y), f"• {m_name}", fill=_TEXT_DARK, font=self.fonts["small"])

        # Outer frame
        draw.rectangle([0, 0, width - 1, height - 1], outline=_FRAME_DARK, width=2)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[list[dict]] = None) -> io.BytesIO:
        """Generates a classic Fire Red/BW2 style trainer card image."""
        width, height = 480, 280
        canvas = self.asset_loader.get_background("trainer_card_bg", width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # 1. Header Title: "TRAINER CARD" centered in the blue header banner (y: 6 to 42)
        title_text = "TRAINER CARD"
        bbox = draw.textbbox((0, 0), title_text, font=self.fonts["title"])
        tx = (width - (bbox[2] - bbox[0])) // 2
        ty = 6 + (30 - (bbox[3] - bbox[1])) // 2
        draw.text((tx, ty), title_text, fill=(255, 203, 5, 255), font=self.fonts["title"])  # Pokemon Yellow

        # 2. Main Details Panel (left column)
        self._draw_classic_panel(draw, 14, 48, 332, 188, fill=(248, 248, 240), border=_FRAME_DARK, border_width=2)

        # Draw Name
        draw.text((24, 56), "NAME:", fill=_FRAME_MID, font=self.fonts["small_bold"])
        draw.text((65, 54), username, fill=_TEXT_DARK, font=self.fonts["body_bold"])

        # Draw ID No. (last 5 digits of discord id)
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((240, 56), f"IDNo. {id_no}", fill=_TEXT_DARK, font=self.fonts["small_bold"])

        # Separator Line
        draw.line([(20, 76), (326, 76)], fill=_FRAME_MID, width=1)

        # Detail lines
        total = wins + losses
        win_rate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"
        rank_val = f"#{rank}" if rank else "Unranked"

        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("RANK", rank_val),
            ("RECORD", f"{wins}W / {losses}L ({win_rate})"),
            ("ACTIVE TEAM", f"{active_team}"),
        ]

        dy = 82
        for label, val in info_items:
            # Draw label
            draw.text((24, dy), label, fill=_FRAME_MID, font=self.fonts["small_bold"])
            # Draw value aligned to the right (x=320)
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((320 - val_w, dy), val, fill=_TEXT_DARK, font=self.fonts["small_bold"])
            dy += 20

        # 3. Avatar Panel
        self._draw_classic_panel(draw, 346, 48, 466, 168, fill=(240, 240, 232), border=_FRAME_DARK, border_width=2)

        # Draw Avatar Image if available
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                # Center avatar inside the frame
                avatar_img = avatar_img.resize((112, 112), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (350, 52), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            # Draw a classic retro Pokéball silhouette in the avatar frame as fallback
            cx, cy = 346 + 60, 48 + 60
            r = 35
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(224, 220, 208), outline=_FRAME_MID, width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=_FRAME_MID, width=2)
            draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(240, 240, 232), outline=_FRAME_MID, width=2)

        # 4. Active Team Section (6 slots)
        self._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(240, 240, 232), border=_FRAME_DARK, border_width=2)

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ..core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            # Draw slot border
            self._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(248, 248, 240), border=_FRAME_MID, border_width=1, radius=3)

            poke_id = None
            if party_pokemon and idx < len(party_pokemon):
                poke = party_pokemon[idx]
                pokname = poke.get("pokname", "")
                if pokname:
                    form_info = FORMS.get(pokname.lower())
                    if form_info:
                        poke_id = form_info.get("pokemon_id")

            if poke_id:
                sprite = self._load_sprite(poke_id, (48, 48))
                if sprite:
                    canvas.paste(sprite, (sx + 4, sy + 4), sprite)
            else:
                # Draw a tiny faint Pokéball silhouette for empty slots
                cx, cy = sx + 28, sy + 28
                r = 12
                faint_outline = (200, 200, 200, 255)
                faint_fill = (248, 248, 240, 255)
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=faint_fill, outline=faint_outline, width=1)
                draw.line([cx - r, cy, cx + r, cy], fill=faint_outline, width=1)
                draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=faint_fill, outline=faint_outline, width=1)

        # Output to buffer
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
