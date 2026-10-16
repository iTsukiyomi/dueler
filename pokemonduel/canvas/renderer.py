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
            fonts["battle_turn"] = ImageFont.truetype(font_file, 20)
            fonts["battle_name"] = ImageFont.truetype(font_file, 14)
            fonts["battle_hp"]   = ImageFont.truetype(font_file, 14)
            fonts["battle_field"]= ImageFont.truetype(font_file, 12)
            fonts["battle_badge"]= ImageFont.truetype(font_file, 11)
        except Exception:
            default = ImageFont.load_default()
            for key in ("title", "body", "body_bold", "small", "small_bold", "badge",
                        "tiny", "hp_label", "pixel_title", "pixel_label", "pixel_sub", "pixel_name",
                        "battle_turn", "battle_name", "battle_hp", "battle_field", "battle_badge"):
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
        """Modern-retro monochrome HUD card with colored status and stat multiplier badges."""
        if not poke:
            return

        w, h = 540, 138

        # Dark sleek panel background
        draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(14, 16, 22, 245), outline=(85, 96, 118, 255), width=2)
        draw.rounded_rectangle([x + 3, y + 3, x + w - 3, y + h - 3], radius=6, outline=(35, 40, 50, 255), width=1)

        # Corner bracket accents (retro arcade look)
        c_len = 12
        for (cx, cy, dx, dy) in [(x + 3, y + 3, 1, 1), (x + w - 3, y + 3, -1, 1),
                                 (x + 3, y + h - 3, 1, -1), (x + w - 3, y + h - 3, -1, -1)]:
            draw.line([(cx, cy), (cx + dx * c_len, cy)], fill=(220, 230, 245, 255), width=2)
            draw.line([(cx, cy), (cx, cy + dy * c_len)], fill=(220, 230, 245, 255), width=2)

        # ── Nickname and Species name in brackets ──────────────────────────
        nick_text = getattr(poke, '_nickname', None)
        species_raw = getattr(poke, '_name', getattr(poke, 'name', '')) or ''
        species_clean = str(species_raw).replace('-', ' ').upper()

        if nick_text and str(nick_text).strip() and str(nick_text).lower() != "none" and str(nick_text).upper() != species_clean:
            display_name = f"{str(nick_text).upper()} ({species_clean})"
        else:
            display_name = species_clean

        f_name = self.fonts.get("battle_name", self.fonts.get("title", self.fonts["body"]))
        f_hp = self.fonts.get("battle_hp", self.fonts["body"])
        f_badge = self.fonts.get("battle_badge", self.fonts["small"])
        f_field = self.fonts.get("battle_field", self.fonts["small"])

        # ── Level & Gender ─────────────────────────────────────────────────
        level = getattr(poke, 'level', 100)
        level_str = f"Lv.{level}"
        lb = draw.textbbox((0, 0), level_str, font=f_name)
        lvl_w = lb[2] - lb[0]

        gender = getattr(poke, 'gender', '')
        gender_w = 0
        gender_label = ""
        gender_color = (255, 255, 255, 255)
        if gender == '-m':
            gender_label = "M"
            gender_color = (90, 170, 255, 255)
            gb = draw.textbbox((0, 0), gender_label, font=f_badge)
            gender_w = (gb[2] - gb[0]) + 8
        elif gender == '-f':
            gender_label = "F"
            gender_color = (255, 120, 160, 255)
            gb = draw.textbbox((0, 0), gender_label, font=f_badge)
            gender_w = (gb[2] - gb[0]) + 8

        right_reserved = lvl_w + (gender_w + 10 if gender_w else 0) + 24
        max_name_w = w - 20 - right_reserved

        # Dynamically measure and truncate name with ellipsis if needed
        while len(display_name) > 3:
            nbb = draw.textbbox((0, 0), display_name, font=f_name)
            if (nbb[2] - nbb[0]) <= max_name_w:
                break
            if display_name.endswith("…"):
                display_name = display_name[:-2] + "…"
            else:
                display_name = display_name[:-1] + "…"

        draw.text((x + 20, y + 20), display_name, fill=(255, 255, 255, 255), font=f_name)

        lvl_x = x + w - 20 - lvl_w
        draw.text((lvl_x, y + 20), level_str, fill=(200, 215, 235, 255), font=f_name)

        if gender_label:
            gx = lvl_x - gender_w - 10
            gh = 18
            draw.rounded_rectangle([gx, y + 18, gx + gender_w, y + 18 + gh], radius=3, fill=(*gender_color[:3], 35), outline=gender_color, width=1)
            draw.text((gx + 4, y + 21), gender_label, fill=gender_color, font=f_badge)

        # ── HP Bar Row ─────────────────────────────────────────────────────
        bar_y = y + 58
        draw.text((x + 20, bar_y - 1), "HP:", fill=(180, 190, 205, 255), font=f_field)

        bar_x = x + 62
        bar_w = w - 240
        bar_h = 16

        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=4, fill=(35, 38, 46, 255), outline=(60, 68, 80, 255), width=1)

        max_hp = getattr(poke, 'starting_hp', 1) or 1
        current_hp = max(0, getattr(poke, 'hp', 0))
        ratio = max(0.0, min(1.0, current_hp / max_hp if max_hp > 0 else 0.0))

        if ratio > 0.0:
            fill_w = max(6, int(bar_w * ratio))
            if ratio > 0.5:
                hp_col = (50, 215, 75, 255)
            elif ratio > 0.2:
                hp_col = (255, 205, 30, 255)
            else:
                hp_col = (245, 50, 50, 255)
            draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=4, fill=hp_col)

        hp_num_str = f"{current_hp}/{max_hp}"
        nb = draw.textbbox((0, 0), hp_num_str, font=f_hp)
        draw.text((x + w - 20 - (nb[2] - nb[0]), bar_y - 1), hp_num_str, fill=(245, 250, 255, 255), font=f_hp)

        # ── Badges Row: Colored Status and Stat Multipliers ───────────────
        badge_y = y + 94
        bx = x + 20

        # Status badge (yellow for para, red for burn, purple for psn, cyan for frz, blue for slp)
        STATUS_MAP = {
            'brn': ((235, 65, 45), (255, 120, 90), 'BRN'),
            'par': ((240, 195, 25), (255, 230, 100), 'PAR'),
            'psn': ((165, 65, 185), (225, 130, 245), 'PSN'),
            'tox': ((135, 45, 205), (185, 100, 255), 'TOX'),
            'slp': ((65, 125, 235), (135, 185, 255), 'SLP'),
            'frz': ((65, 205, 225), (145, 245, 255), 'FRZ'),
        }

        nv = getattr(poke, 'nv', None)
        status_cur = getattr(nv, 'current', None)
        if status_cur and str(status_cur).lower() in STATUS_MAP:
            bg_col, txt_col, label = STATUS_MAP[str(status_cur).lower()]
            sb = draw.textbbox((0, 0), label, font=f_badge)
            sw = (sb[2] - sb[0]) + 16
            sh = 26
            draw.rounded_rectangle([bx, badge_y, bx + sw, badge_y + sh], radius=6, fill=(*bg_col, 50), outline=bg_col, width=2)
            draw.text((bx + 8, badge_y + 6), label, fill=txt_col, font=f_badge)
            bx += sw + 10

        # Stat stage badges (green for positive buffs, red for negative debuffs)
        stages = getattr(poke, 'stages', {})
        if stages:
            STAGE_MULT = {
                1: '1.5x', 2: '2.0x', 3: '2.5x', 4: '3.0x', 5: '3.5x', 6: '4.0x',
                -1: '0.67x', -2: '0.5x', -3: '0.4x', -4: '0.33x', -5: '0.29x', -6: '0.25x'
            }
            stage_items = [(k, v) for k, v in stages.items() if v != 0][:3]
            for stat, val in stage_items:
                is_pos = val > 0
                sign = '+' if is_pos else '-'
                mult = STAGE_MULT.get(val, f"{abs(val)}stg")
                lbl = f"{sign}{mult} {stat.upper()}"
                stb = draw.textbbox((0, 0), lbl, font=f_badge)
                stw = (stb[2] - stb[0]) + 14
                sth = 26
                if is_pos:
                    # Green positive badge
                    draw.rounded_rectangle([bx, badge_y, bx + stw, badge_y + sth], radius=6, fill=(30, 140, 60, 50), outline=(40, 210, 85, 255), width=2)
                    draw.text((bx + 7, badge_y + 6), lbl, fill=(80, 245, 125, 255), font=f_badge)
                else:
                    # Red negative badge
                    draw.rounded_rectangle([bx, badge_y, bx + stw, badge_y + sth], radius=6, fill=(160, 30, 30, 50), outline=(240, 55, 55, 255), width=2)
                    draw.text((bx + 7, badge_y + 6), lbl, fill=(255, 110, 110, 255), font=f_badge)
                bx += stw + 8

    def _draw_terrain_overlay(self, draw: ImageDraw.ImageDraw, terrain: str, width: int, height: int) -> None:
        """Draw subtle terrain aura indicators on the battlefield."""
        terrain_low = terrain.lower().strip()
        if terrain_low in ("normal", "clear", "none"):
            return

        horizon_y = int(height * 0.48)

        if "electric" in terrain_low:
            for dy in range(horizon_y + 20, height - 20, 45):
                for dx in range(40, width - 40, 60):
                    draw.ellipse([dx, dy, dx + 3, dy + 3], fill=(248, 210, 50, 85))
        elif "grassy" in terrain_low:
            for dy in range(horizon_y + 20, height - 20, 45):
                for dx in range(40, width - 40, 60):
                    draw.ellipse([dx, dy, dx + 3, dy + 3], fill=(70, 210, 70, 85))
        elif "misty" in terrain_low:
            for y in range(height - 80, height, 10):
                draw.line([(0, y), (width, y)], fill=(248, 200, 248, 20), width=3)
        elif "psychic" in terrain_low:
            for dy in range(horizon_y + 20, height - 20, 45):
                for dx in range(40, width - 40, 60):
                    draw.ellipse([dx, dy, dx + 3, dy + 3], fill=(248, 90, 140, 85))

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
            for _ in range(100):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(16, 32)
                draw.line([(rx, ry), (rx - 5, ry + length)], fill=(160, 200, 240, 130), width=2)

        elif "sandstorm" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(200, 176, 120, 30))
            for _ in range(120):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(10, 24)
                draw.line([(rx, ry), (rx + length, ry + 2)], fill=(176, 152, 96, 90), width=2)

        elif "hail" in weather_low or "snow" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(200, 230, 255, 15))
            for _ in range(60):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                r = rnd.randint(2, 4)
                draw.ellipse([rx-r, ry-r, rx+r, ry+r], fill=(255, 255, 255, 170))

        canvas.alpha_composite(overlay)


    def render_battle_screen(self, battle) -> io.BytesIO:
        """Generates a high-definition modern-retro Pokémon battle screen (1440x810) with clear, high-legibility UI."""
        width, height = 1440, 810

        canvas = Image.new("RGBA", (width, height), (18, 20, 24, 255))
        draw = ImageDraw.Draw(canvas)

        # Smooth dark monochrome gradient
        for y in range(height):
            t = y / height
            r = int(16 + 10 * t)
            g = int(18 + 12 * t)
            b = int(22 + 15 * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Depth horizon line
        draw.line([(0, int(height * 0.48)), (width, int(height * 0.48))], fill=(28, 33, 42, 255), width=2)

        # Subtle dark pedestals
        # Player pedestal (left foreground)
        draw.ellipse([80, 580, 650, 750], fill=(26, 30, 38, 255), outline=(65, 75, 92, 255), width=3)
        draw.ellipse([120, 600, 610, 730], outline=(40, 48, 60, 255), width=2)

        # Opponent pedestal (right background)
        draw.ellipse([800, 340, 1320, 480], fill=(23, 27, 34, 255), outline=(55, 65, 80, 255), width=3)
        draw.ellipse([835, 355, 1285, 465], outline=(38, 45, 55, 255), width=2)

        weather = getattr(battle.weather, "_weather_type", "clear") or "clear"
        terrain = getattr(battle.terrain, "item", "normal") or "normal"

        self._draw_terrain_overlay(draw, terrain, width, height)

        t1_poke = getattr(battle.trainer1, 'current_pokemon', None)
        t2_poke = getattr(battle.trainer2, 'current_pokemon', None)

        t1_id = getattr(t1_poke, 'pokemon_id', getattr(t1_poke, 'id', None))
        t2_id = getattr(t2_poke, 'pokemon_id', getattr(t2_poke, 'id', None))
        t1_name = getattr(t1_poke, '_name', getattr(t1_poke, 'name', None)) if t1_poke else None
        t2_name = getattr(t2_poke, '_name', getattr(t2_poke, 'name', None)) if t2_poke else None

        sprite_w, sprite_h = 280, 280

        # Player sprite on left platform
        sprite_left = self._load_sprite(t1_id, (sprite_w, sprite_h), name=t1_name, resample=Image.Resampling.NEAREST)
        if sprite_left:
            canvas.paste(sprite_left, (240, 400), sprite_left)
        else:
            draw.rectangle([240, 420, 420, 600], fill=(40, 48, 60, 100), outline=(65, 75, 90, 255), width=2)
            draw.text((310, 480), "?", fill=(180, 190, 210, 255), font=self.fonts["pixel_title"])

        # Opponent sprite on right platform
        sprite_right = self._load_sprite(t2_id, (sprite_w, sprite_h), name=t2_name, resample=Image.Resampling.NEAREST)
        if sprite_right:
            sprite_right = sprite_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            canvas.paste(sprite_right, (905, 165), sprite_right)
        else:
            draw.rectangle([940, 200, 1120, 380], fill=(40, 48, 60, 100), outline=(65, 75, 90, 255), width=2)
            draw.text((1010, 260), "?", fill=(180, 190, 210, 255), font=self.fonts["pixel_title"])

        self._apply_weather_overlay(canvas, weather)

        # ── Top Center: Turn and Weather/Terrain Field Box ─────────────────
        top_box_w, top_box_h = 460, 84
        top_box_x = (width - top_box_w) // 2
        top_box_y = 26

        draw.rounded_rectangle([top_box_x, top_box_y, top_box_x + top_box_w, top_box_y + top_box_h],
                               radius=8, fill=(14, 16, 22, 240), outline=(80, 90, 108, 255), width=2)
        draw.rounded_rectangle([top_box_x + 3, top_box_y + 3, top_box_x + top_box_w - 3, top_box_y + top_box_h - 3],
                               radius=6, outline=(35, 40, 50, 255), width=1)

        f_hdr = self.fonts.get("battle_turn", self.fonts.get("pixel_title", self.fonts["body_bold"]))
        f_sub = self.fonts.get("battle_field", self.fonts.get("pixel_sub", self.fonts["tiny"]))

        turn = getattr(battle, 'turn', 1)
        turn_text = f"TURN {turn:02d}"
        tb = draw.textbbox((0, 0), turn_text, font=f_hdr)
        draw.text((top_box_x + (top_box_w - (tb[2] - tb[0])) // 2, top_box_y + 14),
                  turn_text, fill=(255, 255, 255, 255), font=f_hdr)

        field_parts = []
        if weather and str(weather).lower() not in ("clear", "none", ""):
            field_parts.append(f"WEATHER: {str(weather).replace('-', ' ').upper()}")
        if terrain and str(terrain).lower() not in ("normal", "clear", "none", ""):
            field_parts.append(f"TERRAIN: {str(terrain).replace('-', ' ').upper()}")
        if not field_parts:
            field_text = "WEATHER: CLEAR"
        else:
            field_text = " | ".join(field_parts)

        fb = draw.textbbox((0, 0), field_text, font=f_sub)
        draw.text((top_box_x + (top_box_w - (fb[2] - fb[0])) // 2, top_box_y + 50),
                  field_text, fill=(160, 180, 215, 255), font=f_sub)

        # ── HUD Cards ──────────────────────────────────────────────────────
        hud_w, hud_h = 540, 138
        # Player HUD at top-left
        self._draw_hud(draw, 44, 110, t1_poke, is_left=True)

        # Opponent HUD at bottom-right
        self._draw_hud(draw, width - hud_w - 44, height - hud_h - 44, t2_poke, is_left=False)

        # Outer border
        draw.rectangle([0, 0, width - 1, height - 1], outline=(55, 62, 75, 255), width=2)

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
