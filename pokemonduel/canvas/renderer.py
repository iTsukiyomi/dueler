import io
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from .assets import AssetLoader

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

_TYPE_ID_TO_NAME = {
    1: "Normal", 2: "Fighting", 3: "Flying", 4: "Poison", 5: "Ground",
    6: "Rock", 7: "Bug", 8: "Ghost", 9: "Steel", 10: "Fire",
    11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
    16: "Dragon", 17: "Dark", 18: "Fairy",
}

from .themes.palette import DEFAULT_PALETTE, ThemePalette


class BattleRenderer:
    """Classic Pokémon-style canvas rendering pipeline for battle screens, teams, and profiles."""

    def __init__(self, data_dir: Path, palette: ThemePalette = DEFAULT_PALETTE, theme: str = "firered") -> None:
        self.palette = palette
        self.data_dir = data_dir
        self.theme = theme.lower()

        theme_lower = self.theme.strip()
        if theme_lower == "firered":
            self.gen = 3
        elif theme_lower in ("heartgold", "platinum"):
            self.gen = 4
        elif theme_lower == "black":
            self.gen = 5
        elif theme_lower in ("x", "sun"):
            self.gen = 6
        else:
            self.gen = 8

        self.sprite_dir = data_dir / "img"
        self.asset_loader = AssetLoader(data_dir / "canvas_assets")
        self.fonts = self._load_fonts()

    def _ensure_font(self, font_name: str, url: str) -> Optional[Path]:
        """Ensures that a font exists locally, downloading it from the given URL if missing."""
        font_dir = self.data_dir / "fonts"
        try:
            font_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None

        font_path = font_dir / font_name
        if font_path.exists():
            return font_path

        import urllib.request
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(font_path, "wb") as f:
                    f.write(response.read())
            return font_path
        except Exception:
            if font_path.exists():
                try:
                    font_path.unlink()
                except Exception:
                    pass
            return None

    def _load_fonts(self) -> dict[str, ImageFont.ImageFont]:
        """Load authentic Pokémon 8-bit arcade pixel font (Press Start 2P) across the bot."""
        pixel_path = self.data_dir / "fonts" / "PressStart2P-Regular.ttf"
        if not pixel_path.exists():
            pixel_path = self._ensure_font(
                "PressStart2P-Regular.ttf",
                "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"
            )

        font_file = str(pixel_path) if (pixel_path and Path(pixel_path).exists()) else "arial.ttf"

        fonts = {}
        try:
            fonts["title"]       = ImageFont.truetype(font_file, 16)
            fonts["body"]        = ImageFont.truetype(font_file, 10)
            fonts["body_bold"]   = ImageFont.truetype(font_file, 10)
            fonts["small"]       = ImageFont.truetype(font_file, 8)
            fonts["small_bold"]  = ImageFont.truetype(font_file, 8)
            fonts["badge"]       = ImageFont.truetype(font_file, 7)
            fonts["tiny"]        = ImageFont.truetype(font_file, 7)
            fonts["hp_label"]    = ImageFont.truetype(font_file, 8)
            fonts["pixel_title"] = ImageFont.truetype(font_file, 24)
            fonts["pixel_label"] = ImageFont.truetype(font_file, 12)
            fonts["pixel_sub"]   = ImageFont.truetype(font_file, 11)
            fonts["pixel_name"]  = ImageFont.truetype(font_file, 10)
        except Exception:
            default = ImageFont.load_default()
            for key in ("title", "body", "body_bold", "small", "small_bold", "badge",
                        "tiny", "hp_label", "pixel_title", "pixel_label", "pixel_sub", "pixel_name"):
                fonts[key] = default

        return fonts

    def _load_sprite(self, poke_id: Optional[int], size: Tuple[int, int], name: Optional[str] = None, resample: Optional[Image.Resampling] = None) -> Optional[Image.Image]:
        """Safely loads and scales a Pokémon sprite from disk.

        Attempts to load in order:
        1. Specific form ID (form_info['id'])
        2. Form variety ID (form_info['pokemon_id'])
        3. Base species ID (form_info['base_id'])
        4. Fallback passed poke_id
        """
        candidates = []
        if name:
            try:
                from ..core.registry import FORMS
                form_info = FORMS.get(name.lower())
                if form_info:
                    fid = form_info.get("id")
                    if fid and fid not in candidates:
                        candidates.append(fid)
                    pid = form_info.get("pokemon_id")
                    if pid and pid not in candidates:
                        candidates.append(pid)
                    bid = form_info.get("base_id")
                    if bid and bid not in candidates:
                        candidates.append(bid)
            except Exception:
                pass

        if poke_id and poke_id not in candidates:
            candidates.append(poke_id)

        resample_mode = resample if resample is not None else (Image.Resampling.NEAREST if self.gen <= 5 else Image.Resampling.LANCZOS)

        for cid in candidates:
            for ext in ("png", "gif", "jpg"):
                path = self.sprite_dir / f"{cid}.{ext}"
                if path.exists():
                    try:
                        img = Image.open(path).convert("RGBA")
                        if getattr(img, "is_animated", False):
                            img.seek(0)
                            img = img.convert("RGBA")
                        img = img.resize(size, resample_mode)
                        return img
                    except Exception:
                        continue
        return None


    def _draw_classic_panel(self, draw: ImageDraw.ImageDraw,
                            x1: float, y1: float, x2: float, y2: float,
                            *, fill=None, border=None, border_width: int = 2,
                            radius: int = 4) -> None:
        """Draw a classic Pokémon-style bordered panel (solid fill, dark border)."""
        fill = fill or self.palette.panel_bg
        border = border or self.palette.frame_dark

        if self.theme in ("firered", "black"):
            radius = 0

        if self.theme == "firered":
            draw.rectangle([x1, y1, x2, y2], fill=(*fill, 255) if len(fill) == 3 else fill)
            draw.rectangle([x1, y1, x2, y2], outline=(*border, 255) if len(border) == 3 else border, width=2)
            draw.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], outline=(*border, 255) if len(border) == 3 else border, width=1)
            return

        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(*fill, 255) if len(fill) == 3 else fill)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=(*border, 255) if len(border) == 3 else border, width=border_width)

    def _draw_header_bar(self, draw: ImageDraw.ImageDraw,
                         x1: float, y1: float, x2: float, height: int = 24,
                         text: str = "", *, bg=None) -> None:
        """Draw a classic dark header bar with white text (Gen 3/5 style)."""
        bg = bg or self.palette.header_bg
        radius = 0 if self.theme in ("firered", "black") else 4

        if self.theme == "firered":
            draw.rectangle([x1, y1, x2, y1 + height], fill=(*bg, 255) if len(bg) == 3 else bg)
            draw.rectangle([x1, y1, x2, y1 + height], outline=self.palette.frame_dark, width=1)
        else:
            draw.rounded_rectangle([x1, y1, x2, y1 + height], radius=radius, fill=(*bg, 255) if len(bg) == 3 else bg)

        if text:
            font = self.fonts["body_bold"]
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = x1 + ((x2 - x1) - (bbox[2] - bbox[0])) // 2
            ty = y1 + (height - (bbox[3] - bbox[1])) // 2 - 1
            draw.text((tx, ty), text, fill=self.palette.header_text, font=font)

    def _draw_type_badge(self, draw: ImageDraw.ImageDraw,
                         x: float, y: float, type_name: str,
                         *, width: int = 60, height: int = 18) -> Tuple[float, float]:
        """Draw a classic Gen 3/5 style type rectangle badge."""
        font = self.fonts.get("badge", self.fonts["small_bold"])
        label = type_name.upper()

        if self.theme == "firered":
            draw.rectangle([x, y, x + width, y + height], fill=self.palette.panel_bg, outline=self.palette.frame_dark, width=1)
            bbox = draw.textbbox((0, 0), label, font=font)
            tx = x + (width - (bbox[2] - bbox[0])) // 2
            ty = y + (height - (bbox[3] - bbox[1])) // 2 - 1
            draw.text((tx, ty), label, fill=self.palette.text_dark, font=font)
            return width, height

        color = TYPE_COLORS.get(type_name.lower(), (128, 128, 128, 255))
        radius = 3

        draw.rounded_rectangle([x, y, x + width, y + height], radius=radius,
                               fill=color, outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40), 255), width=1)

        bbox = draw.textbbox((0, 0), label, font=font)
        tx = x + (width - (bbox[2] - bbox[0])) // 2
        ty = y + (height - (bbox[3] - bbox[1])) // 2 - 1

        draw.text((tx + 1, ty + 1), label, fill=(0, 0, 0, 100), font=font)
        draw.text((tx, ty), label, fill=(255, 255, 255, 255), font=font)

        return width, height

    def _draw_status_badge(self, draw: ImageDraw.ImageDraw,
                           x: float, y: float, status: str) -> Tuple[float, float]:
        """Draw a classic Gen 5 style status label (BRN, PAR, etc.)."""
        status_clean = status.lower().strip()
        badge_text = status_clean[:3].upper()
        color = STATUS_COLORS.get(status_clean, (128, 128, 128, 255))

        font = self.fonts.get("badge", self.fonts["small_bold"])
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_w = bbox[2] - bbox[0]
        w = text_w + 10
        h = 16

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

        font = self.fonts["hp_label"]
        draw.text((x - 24, y - 1), "HP:", fill=self.palette.text_dark, font=font)

        draw.rounded_rectangle([x, y, x + w, y + h], radius=2, fill=self.palette.hp_bg)

        if ratio > 0.0:
            fill_w = max(3, int(w * ratio))
            if ratio > 0.5:
                color = self.palette.hp_green
            elif ratio > 0.2:
                color = self.palette.hp_yellow
            else:
                color = self.palette.hp_red
            draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=2, fill=color)

        draw.rounded_rectangle([x, y, x + w, y + h], radius=2, outline=self.palette.hp_border, width=1)

        hp_text = f"{current}/{maximum}"
        hp_font = self.fonts["small"]
        draw.text((x + w + 6, y - 2), hp_text, fill=self.palette.text_dark, font=hp_font)

    def _draw_hud(self, draw: ImageDraw.ImageDraw,
                  x: float, y: float, poke, is_left: bool) -> None:
        """Classic Gen 3/5 HUD card for an active Pokémon."""
        width = 310
        height = 80

        self._draw_classic_panel(draw, x, y, x + width, y + height,
                                 fill=None, border=None)

        name_text = poke._name.replace('-', ' ').title()
        nick_text = getattr(poke, '_nickname', None)
        display_name = nick_text if nick_text and nick_text != "None" else name_text

        font_name = self.fonts["body_bold"]
        draw.text((x + 10, y + 8), display_name, fill=self.palette.text_dark, font=font_name)

        level = getattr(poke, 'level', 100)
        level_text = f"Lv{level}"
        font_small = self.fonts["body"]
        lv_bbox = draw.textbbox((0, 0), level_text, font=font_small)
        lv_x = x + width - (lv_bbox[2] - lv_bbox[0]) - 10
        draw.text((lv_x, y + 8), level_text, fill=self.palette.text_mid, font=font_small)

        gender = getattr(poke, 'gender', '')
        if gender == '-m':
            draw.text((lv_x - 16, y + 8), "♂", fill=(80, 128, 240, 255), font=font_small)
        elif gender == '-f':
            draw.text((lv_x - 16, y + 8), "♀", fill=(240, 104, 128, 255), font=font_small)

        max_hp = poke.starting_hp
        current_hp = max(0, poke.hp)
        self._draw_hp_bar(draw, x + 38, y + 36, width - 110, 8, current_hp, max_hp)

        curr_y = y + 54
        start_x = x + 10
        if poke.nv.current:
            badge_w, _ = self._draw_status_badge(draw, start_x, curr_y, poke.nv.current)
            start_x += badge_w + 6

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
                draw.text((start_x, curr_y + 1), stages_text, fill=self.palette.text_mid, font=self.fonts["small"])

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
            draw.rectangle([0, 0, width, height], fill=(255, 200, 80, 18))

        elif "rain" in weather_low:
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

        plat_left_cx, plat_left_cy = 230, 400
        draw.ellipse([plat_left_cx - 120, plat_left_cy - 20, plat_left_cx + 120, plat_left_cy + 20],
                     fill=(96, 160, 56, 80), outline=(56, 120, 40, 180), width=2)

        plat_right_cx, plat_right_cy = 730, 380
        draw.ellipse([plat_right_cx - 110, plat_right_cy - 18, plat_right_cx + 110, plat_right_cy + 18],
                     fill=(96, 160, 56, 80), outline=(56, 120, 40, 180), width=2)

        self._draw_terrain_overlay(draw, terrain, width, height)

        t1_poke = battle.trainer1.current_pokemon
        t2_poke = battle.trainer2.current_pokemon

        t1_id = getattr(t1_poke, 'pokemon_id', getattr(t1_poke, 'id', None))
        t2_id = getattr(t2_poke, 'pokemon_id', getattr(t2_poke, 'id', None))
        t1_name = getattr(t1_poke, '_name', getattr(t1_poke, 'name', None)) if t1_poke else None
        t2_name = getattr(t2_poke, '_name', getattr(t2_poke, 'name', None)) if t2_poke else None

        sprite_w, sprite_h = 200, 200

        sprite_left = self._load_sprite(t1_id, (sprite_w, sprite_h), name=t1_name)
        if sprite_left:
            canvas.paste(sprite_left, (130, 230), sprite_left)
        else:
            draw.rectangle([170, 260, 290, 380], fill=(80, 140, 60, 60), outline=(56, 120, 40, 160))
            draw.text((215, 310), "?", fill=self.palette.text_mid, font=self.fonts["title"])

        sprite_right = self._load_sprite(t2_id, (sprite_w - 10, sprite_h - 10), name=t2_name)
        if sprite_right:
            sprite_right = sprite_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            canvas.paste(sprite_right, (635, 210), sprite_right)
        else:
            draw.rectangle([670, 250, 790, 370], fill=(80, 140, 60, 60), outline=(56, 120, 40, 160))
            draw.text((715, 300), "?", fill=self.palette.text_mid, font=self.fonts["title"])

        self._apply_weather_overlay(canvas, weather)

        self._draw_hud(draw, 560, 30, t2_poke, is_left=False)
        self._draw_hud(draw, 50, 440, t1_poke, is_left=True)

        info_w, info_h = 160, 60
        info_x = (width - info_w) // 2
        info_y = 16
        self._draw_classic_panel(draw, info_x, info_y, info_x + info_w, info_y + info_h,
                                 fill=None, border=None)

        turn = getattr(battle, 'turn', 1)
        turn_text = f"TURN {turn}"
        tb = draw.textbbox((0, 0), turn_text, font=self.fonts["body_bold"])
        draw.text((info_x + (info_w - (tb[2] - tb[0])) // 2, info_y + 6),
                  turn_text, fill=self.palette.text_dark, font=self.fonts["body_bold"])

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

        draw.rectangle([0, 0, width - 1, height - 1], outline=self.palette.frame_dark, width=3)
        draw.rectangle([3, 3, width - 4, height - 4], outline=self.palette.frame_mid, width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_team_preview(self, battle) -> io.BytesIO:
        """Generates a Pokémon-style team preview screen with a completely transparent background.

        Matches the reference design:
        - 100% transparent canvas (zero background, no panels, no cell backgrounds)
        - Authentic Pokémon pixel font (Press Start 2P)
        - Shows dynamic user vs opponent name at top-right
        - Sprites float cleanly on transparent canvas
        - Uppercase pixel-font names below sprites
        - Dotted divider line separating the two teams
        """
        W, H = 1024, 560
        MARGIN = 40

        # ── 100% Completely Transparent Canvas ─────────────────────────────
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        f_title = self.fonts.get("pixel_title", self.fonts["title"])
        f_label = self.fonts.get("pixel_label", self.fonts["body_bold"])
        f_sub   = self.fonts.get("pixel_sub", self.fonts["small_bold"])
        f_name  = self.fonts.get("pixel_name", self.fonts["small"])

        # Helper for crisp outlined text (guarantees readability on both Discord dark & light mode)
        def _draw_text_with_outline(pos, text, font, fill=(255, 255, 255, 255), outline=(0, 0, 0, 220)):
            x, y = pos
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                draw.text((x + dx, y + dy), text, fill=outline, font=font)
            draw.text((x, y), text, fill=fill, font=font)

        # ── Title ──────────────────────────────────────────────────────────
        _draw_text_with_outline((MARGIN, 36), "TEAM PREVIEW", f_title, fill=(255, 255, 255, 255))

        # ── Trainer Names (Top Right) ──────────────────────────────────────
        def _get_trainer_name(trainer, default: str) -> str:
            if not trainer:
                return default
            member = getattr(trainer, "member", None)
            if member:
                return getattr(member, "display_name", getattr(member, "name", str(getattr(trainer, "name", default))))
            name = getattr(trainer, "name", None)
            if name:
                return str(name)
            return default

        t1_name = _get_trainer_name(getattr(battle, "trainer1", None), "Trainer")
        t2_name = _get_trainer_name(getattr(battle, "trainer2", None), "Opponent")
        if len(t1_name) > 16:
            t1_name = t1_name[:15] + "…"
        if len(t2_name) > 16:
            t2_name = t2_name[:15] + "…"
        vs_text = f"{t1_name} VS {t2_name}".upper()

        tb = draw.textbbox((0, 0), vs_text, font=f_sub)
        vs_w = tb[2] - tb[0]
        _draw_text_with_outline((W - MARGIN - vs_w, 44), vs_text, f_sub, fill=(210, 225, 245, 255))

        # ── Layout Dimensions ──────────────────────────────────────────────
        AVAILABLE_W = W - 2 * MARGIN
        N_COLS = 6
        COL_W = AVAILABLE_W / N_COLS
        SPRITE_SIZE = 120

        # Section labels
        _draw_text_with_outline((MARGIN, 96), "YOUR TEAM", f_label, fill=(200, 210, 225, 255))
        _draw_text_with_outline((MARGIN, 350), "OPPONENT'S TEAM", f_label, fill=(200, 210, 225, 255))

        # Dotted divider line
        for dx in range(176, 850, 8):
            draw.ellipse([dx, 310, dx + 2, 312], fill=(0, 0, 0, 180))
            draw.ellipse([dx, 311, dx + 2, 313], fill=(200, 215, 235, 255))

        # ── Helper: draw one team row ──────────────────────────────────────
        def _draw_team_row(trainer, sprite_y: int, name_y: int) -> None:
            party = getattr(trainer, "party", [])[:N_COLS] if trainer else []
            for col, poke in enumerate(party):
                cell_cx = MARGIN + int((col + 0.5) * COL_W)

                if isinstance(poke, dict):
                    poke_id   = poke.get("pokemon_id") or poke.get("id") or poke.get("pokid")
                    poke_name = poke.get("pokname") or poke.get("name") or ""
                else:
                    poke_id   = getattr(poke, "pokemon_id", getattr(poke, "id", None))
                    poke_name = getattr(poke, "_name", getattr(poke, "name", "")) or ""

                sprite = self._load_sprite(poke_id, (SPRITE_SIZE, SPRITE_SIZE), name=poke_name, resample=Image.Resampling.NEAREST)
                if sprite:
                    paste_x = cell_cx - sprite.width // 2
                    paste_y = sprite_y + (SPRITE_SIZE - sprite.height)
                    canvas.paste(sprite, (int(paste_x), int(paste_y)), sprite)
                else:
                    _draw_text_with_outline((cell_cx - 8, sprite_y + 40), "?", f_title, fill=(160, 175, 200, 200))

                display = poke_name.replace("-", " ").upper()
                if len(display) > 13:
                    display = display[:12] + "."
                nb = draw.textbbox((0, 0), display, font=f_name)
                nx = cell_cx - (nb[2] - nb[0]) // 2
                _draw_text_with_outline((nx, name_y), display, f_name, fill=(240, 245, 255, 255))

        _draw_team_row(getattr(battle, "trainer1", None), 120, 260)
        _draw_team_row(getattr(battle, "trainer2", None), 376, 516)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def _get_base_stats(self, identifier: str) -> dict[str, int]:
        """Look up base stats from static registries. Fixed to use proper registry API."""
        try:
            from ..core.registry import FORMS, POKEMON_STATS
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
        from .themes import get_theme_renderer
        theme_renderer = get_theme_renderer(self.theme, self)
        return theme_renderer.render_pokemon_card(poke, player_name, type_names)

    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[list[dict]] = None) -> io.BytesIO:
        """Generates a classic trainer card image."""
        from .themes import get_theme_renderer
        theme_renderer = get_theme_renderer(self.theme, self)
        return theme_renderer.render_trainer_card(username, player_id, rank, elo, wins, losses, wallet, active_team, avatar_bytes, party_pokemon)

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True,
                              help_display: str = "image") -> io.BytesIO:
        """Render a classic settings menu image."""
        from .themes import get_theme_renderer
        theme_renderer = get_theme_renderer(self.theme, self)
        return theme_renderer.render_settings_menu(current_theme, moveset_img=moveset_img, help_display=help_display)

    def render_moveset(self, pokemon_name: str, moves_data: list[dict],
                       page: int, total_pages: int, total_moves: int) -> io.BytesIO:
        """Render a themed moveset page image."""
        from .themes import get_theme_renderer
        theme_renderer = get_theme_renderer(self.theme, self)
        return theme_renderer.render_moveset(pokemon_name, moves_data, page, total_pages, total_moves)

    def render_help_page(self, category: str, commands_list: list[dict],
                         page: int, total_pages: int) -> io.BytesIO:
        """Render a themed help page image."""
        from .themes import get_theme_renderer
        theme_renderer = get_theme_renderer(self.theme, self)
        return theme_renderer.render_help_page(category, commands_list, page, total_pages)
