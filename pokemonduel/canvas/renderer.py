import io
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from .assets import AssetLoader

# Type colors for UI borders and accents
TYPE_COLORS = {
    "normal": (168, 167, 122, 255),
    "fire": (240, 128, 48, 255),
    "water": (99, 144, 240, 255),
    "electric": (248, 208, 48, 255),
    "grass": (120, 200, 80, 255),
    "ice": (152, 216, 216, 255),
    "fighting": (192, 48, 40, 255),
    "poison": (160, 64, 160, 255),
    "ground": (224, 192, 104, 255),
    "flying": (168, 144, 240, 255),
    "psychic": (248, 88, 136, 255),
    "bug": (168, 184, 32, 255),
    "rock": (184, 160, 56, 255),
    "ghost": (112, 88, 152, 255),
    "dragon": (112, 56, 248, 255),
    "dark": (112, 88, 72, 255),
    "steel": (184, 184, 208, 255),
    "fairy": (214, 158, 214, 255),
    "stellar": (74, 186, 176, 255),
    "unknown": (104, 160, 144, 255),
}

STATUS_COLORS = {
    "burn": (255, 75, 75, 255),
    "brn": (255, 75, 75, 255),
    "poison": (160, 64, 160, 255),
    "psn": (160, 64, 160, 255),
    "tox": (130, 40, 200, 255),
    "b-poison": (130, 40, 200, 255),
    "paralysis": (240, 196, 25, 255),
    "par": (240, 196, 25, 255),
    "sleep": (74, 144, 226, 255),
    "slp": (74, 144, 226, 255),
    "freeze": (0, 200, 230, 255),
    "frz": (0, 200, 230, 255),
}

class BattleRenderer:
    """Enterprise-grade canvas rendering pipeline for battle screens, teams, and profiles."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sprite_dir = data_dir / "img"
        self.asset_loader = AssetLoader(data_dir / "canvas_assets")
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> dict[str, ImageFont.ImageFont]:
        """Tries to load premium vector fonts from the OS, falling back to default."""
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
                if "Bold" in p:
                    bold_path = p
                else:
                    reg_path = p
                    
        if not bold_path:
            bold_path = reg_path

        fonts = {}
        try:
            fonts["title"] = ImageFont.truetype(bold_path or "arial.ttf", 20)
            fonts["body"] = ImageFont.truetype(reg_path or "arial.ttf", 14)
            fonts["body_bold"] = ImageFont.truetype(bold_path or "arial.ttf", 14)
            fonts["small"] = ImageFont.truetype(reg_path or "arial.ttf", 11)
            fonts["small_bold"] = ImageFont.truetype(bold_path or "arial.ttf", 11)
        except Exception:
            # Fallbacks
            default = ImageFont.load_default()
            # pyrefly: ignore [unsupported-operation]
            fonts["title"] = default
            # pyrefly: ignore [unsupported-operation]
            fonts["body"] = default
            # pyrefly: ignore [unsupported-operation]
            fonts["body_bold"] = default
            # pyrefly: ignore [unsupported-operation]
            fonts["small"] = default
            # pyrefly: ignore [unsupported-operation]
            fonts["small_bold"] = default
            
        # pyrefly: ignore [bad-return]
        return fonts

    def _load_sprite(self, poke_id: Optional[int], size: Tuple[int, int]) -> Optional[Image.Image]:
        """Safely loads and scales a Pokémon sprite from disk."""
        if poke_id is None:
            return None

        # Look in the img directory for matching extensions
        for ext in ("png", "gif", "jpg"):
            path = self.sprite_dir / f"{poke_id}.{ext}"
            if path.exists():
                try:
                    img = Image.open(path).convert("RGBA")
                    # Handle animated GIFs by taking the first frame
                    if getattr(img, "is_animated", False):
                        img.seek(0)
                        img = img.convert("RGBA")
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    return img
                except Exception:
                    continue
        return None

    def _draw_glass_panel(self, draw: ImageDraw.ImageDraw, x1: float, y1: float, x2: float, y2: float, border_color: Tuple[int, int, int, int] = (255, 255, 255, 40)) -> None:
        """Draws a premium semi-transparent panel with thin highlight borders."""
        # Main background fill
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(15, 18, 27, 205))
        # Top-left highlight border
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, outline=border_color, width=1)

    def _draw_status_badge(self, draw: ImageDraw.ImageDraw, x: float, y: float, status: str) -> Tuple[float, float]:
        """Draws a premium rounded status pill (e.g. PAR, BRN). Returns (width, height)."""
        status_clean = status.lower().strip()
        badge_text = status_clean[:3].upper()
        
        color = STATUS_COLORS.get(status_clean, (128, 128, 128, 255))
        
        # Calculate dimensions
        font = self.fonts["small_bold"]
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        w = text_w + 12
        h = 18
        
        # Draw pill shadow/glow
        draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=color)
        draw.text((x + 6, y + (h - text_h) // 2 - 1), badge_text, fill=(255, 255, 255, 255), font=font)
        
        return w, h

    def _draw_hp_bar(self, draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float, current: int, maximum: int) -> None:
        """Draws a sleek, gradient-looking HP bar with status thresholds."""
        ratio = max(0.0, min(1.0, current / maximum if maximum > 0 else 0.0))
        
        # Background bar
        draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=(35, 38, 48, 255))
        
        if ratio > 0.0:
            fill_w = max(4, int(w * ratio))
            # Determine color
            if ratio > 0.5:
                color = (46, 204, 113, 255)  # Soft green
            elif ratio > 0.2:
                color = (241, 196, 15, 255)  # Soft yellow
            else:
                color = (231, 76, 60, 255)   # Soft red
                
            draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=3, fill=color)
            
        # Draw border
        draw.rounded_rectangle([x, y, x + w, y + h], radius=3, outline=(255, 255, 255, 15), width=1)
        
        # HP Text Overlay
        hp_text = f"{current}/{maximum}"
        font = self.fonts["small_bold"]
        bbox = draw.textbbox((0, 0), hp_text, font=font)
        tx = x + (w - (bbox[2] - bbox[0])) // 2
        ty = y + (h - (bbox[3] - bbox[1])) // 2 - 1
        draw.text((tx + 1, ty + 1), hp_text, fill=(0, 0, 0, 160), font=font)
        draw.text((tx, ty), hp_text, fill=(255, 255, 255, 240), font=font)

    def _draw_hud(self, draw: ImageDraw.ImageDraw, x: float, y: float, poke, is_left: bool) -> None:
        """Renders the modular HUD card for a single active Pokémon."""
        width = 330
        height = 92
        
        # Get active type colors for accents
        accent_color = (0, 240, 255, 120) if is_left else (255, 105, 180, 120)
        
        # Draw base panel
        self._draw_glass_panel(draw, x, y, x + width, y + height, border_color=accent_color)
        
        # Left accent vertical stripe
        accent_stripe_w = 4
        draw.rectangle([x, y + 6, x + accent_stripe_w, y + height - 6], fill=accent_color)

        # Name and Nickname
        name_text = poke._name.replace('-', ' ').title()
        nick_text = getattr(poke, '_nickname', None)
        display_name = f"{nick_text}" if nick_text and nick_text != "None" else name_text
        
        font_name = self.fonts["body_bold"]
        draw.text((x + 12, y + 10), display_name, fill=(255, 255, 255, 255), font=font_name)
        
        # Level or Status indicators
        level = getattr(poke, 'level', 100)
        level_text = f"Lv.{level}"
        font_small = self.fonts["small_bold"]
        bbox_name = draw.textbbox((x + 12, y + 10), display_name, font=font_name)
        
        lx = bbox_name[2] + 10
        draw.text((lx, y + 12), level_text, fill=(0, 240, 255, 200) if is_left else (255, 105, 180, 200), font=font_small)

        # HP Bar
        max_hp = poke.starting_hp
        current_hp = max(0, poke.hp)
        self._draw_hp_bar(draw, x + 12, y + 36, width - 24, 18, current_hp, max_hp)

        # Active Status Conditions or Boosts
        curr_y = y + 62
        if poke.nv.current:
            badge_w, _ = self._draw_status_badge(draw, x + 12, curr_y, poke.nv.current)
            start_x = x + 12 + badge_w + 6
        else:
            start_x = x + 12
            
        # Draw simple stat stages indicators if any are boosted/dropped
        stages_info = []
        stages = getattr(poke, 'stages', {})
        if stages:
            for stat, val in stages.items():
                if val != 0:
                    sign = "+" if val > 0 else ""
                    color_tag = "▲" if val > 0 else "▼"
                    stages_info.append(f"{stat.upper()}{sign}{val}{color_tag}")
                    
        if stages_info:
            stages_text = " ".join(stages_info[:3]) # Limit to 3 to avoid overflow
            draw.text((start_x, curr_y + 2), stages_text, fill=(255, 255, 255, 160), font=self.fonts["small"])

    def _draw_terrain_overlay(self, draw: ImageDraw.ImageDraw, terrain: str, width: int, height: int) -> None:
        """Renders glowing terrain rings and highlights around platforms."""
        terrain_low = terrain.lower().strip()
        if terrain_low == "normal" or terrain_low == "clear":
            return
            
        # Draw on bottom half of the screen
        if "electric" in terrain_low:
            draw.ellipse([95, 355, 365, 425], outline=(248, 208, 48, 200), width=2)
            draw.ellipse([595, 355, 865, 425], outline=(248, 208, 48, 200), width=2)
            draw.line([(230, 390), (250, 430), (220, 470)], fill=(248, 208, 48, 150), width=2)
            draw.line([(730, 390), (710, 430), (740, 470)], fill=(248, 208, 48, 150), width=2)
            
        elif "grassy" in terrain_low:
            draw.ellipse([95, 355, 365, 425], outline=(120, 200, 80, 220), width=2)
            draw.ellipse([595, 355, 865, 425], outline=(120, 200, 80, 220), width=2)
            for cx, cy in [(180, 450), (280, 430), (650, 440), (800, 455)]:
                draw.polygon([(cx, cy), (cx - 4, cy - 8), (cx + 4, cy - 8)], fill=(46, 204, 113, 140))
                
        elif "misty" in terrain_low:
            draw.ellipse([95, 355, 365, 425], outline=(214, 158, 214, 180), width=2)
            draw.ellipse([595, 355, 865, 425], outline=(214, 158, 214, 180), width=2)
            for y in range(height - 60, height, 6):
                opacity = int(40 * ((y - (height - 60)) / 60))
                draw.line([(0, y), (width, y)], fill=(255, 200, 255, opacity), width=4)
                
        elif "psychic" in terrain_low:
            draw.ellipse([95, 355, 365, 425], outline=(248, 88, 136, 220), width=2)
            draw.ellipse([595, 355, 865, 425], outline=(248, 88, 136, 220), width=2)
            draw.ellipse([80, 350, 380, 430], outline=(248, 88, 136, 80), width=1)
            draw.ellipse([580, 350, 880, 430], outline=(248, 88, 136, 80), width=1)

    def _apply_weather_overlay(self, canvas: Image.Image, weather: str) -> None:
        """Applies diagonal weather particle overlays and ambient color shading."""
        weather_low = weather.lower().strip()
        if weather_low == "clear" or weather_low == "none":
            return
            
        width, height = canvas.size
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        import random
        rnd = random.Random(42)
        
        if "sun" in weather_low or "sunny" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(255, 200, 0, 20))
            for angle in range(120, 210, 10):
                import math
                rad = math.radians(angle)
                ex = 900 + 1000 * math.cos(rad)
                ey = 0 + 1000 * math.sin(rad)
                draw.line([(900, 0), (ex, ey)], fill=(255, 255, 200, 30), width=15)
                
        elif "rain" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(0, 50, 150, 25))
            for _ in range(80):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(15, 30)
                draw.line([(rx, ry), (rx - length // 2, ry + length)], fill=(174, 219, 240, 150), width=1)
                
        elif "sandstorm" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(210, 180, 140, 40))
            for _ in range(120):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                length = rnd.randint(10, 25)
                draw.line([(rx, ry), (rx + length, ry + length // 3)], fill=(180, 150, 100, 100), width=1)
                
        elif "hail" in weather_low or "snow" in weather_low:
            draw.rectangle([0, 0, width, height], fill=(0, 200, 255, 20))
            for _ in range(60):
                rx = rnd.randint(0, width)
                ry = rnd.randint(0, height)
                radius = rnd.randint(1, 4)
                draw.ellipse([rx - radius, ry - radius, rx + radius, ry + radius], fill=(255, 255, 255, 180))
                
        canvas.alpha_composite(overlay)

    def render_battle_screen(self, battle) -> io.BytesIO:
        """Generates a high-fidelity image representing the active battle state."""
        width, height = 960, 540
        
        # Check active weather, terrain, and Trick Room
        weather = getattr(battle.weather, "_weather_type", "clear") or "clear"
        terrain = getattr(battle.terrain, "item", "normal") or "normal"
        trick_room_active = False
        if hasattr(battle, "trick_room") and battle.trick_room.active():
            trick_room_active = True
            
        bg_name = "trick_room" if trick_room_active else "stadium_cyber"
        canvas = self.asset_loader.get_background(bg_name, width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # 1. Draw Platform bases (cyber platform ellipses)
        # Left (Trainer 1)
        draw.ellipse([100, 360, 360, 420], fill=(0, 240, 255, 30), outline=(0, 240, 255, 100), width=2)
        draw.ellipse([110, 368, 350, 412], fill=(0, 240, 255, 10), outline=(0, 240, 255, 60), width=1)
        
        # Right (Trainer 2)
        draw.ellipse([600, 360, 860, 420], fill=(255, 105, 180, 30), outline=(255, 105, 180, 100), width=2)
        draw.ellipse([610, 368, 850, 412], fill=(255, 105, 180, 10), outline=(255, 105, 180, 60), width=1)

        # Draw terrain overlays
        self._draw_terrain_overlay(draw, terrain, width, height)

        # 2. Draw Active Pokémon Sprites
        t1_poke = battle.trainer1.current_pokemon
        t2_poke = battle.trainer2.current_pokemon

        # Retrieve IDs
        t1_id = getattr(t1_poke, 'pokemon_id', getattr(t1_poke, 'id', None))
        t2_id = getattr(t2_poke, 'pokemon_id', getattr(t2_poke, 'id', None))

        sprite_w, sprite_h = 210, 210

        # Draw left Pokémon (facing right/up)
        sprite_left = self._load_sprite(t1_id, (sprite_w, sprite_h))
        if sprite_left:
            # Shift slightly down-left relative to platform center (230, 390)
            canvas.paste(sprite_left, (125, 210), sprite_left)
        else:
            # Procedural placeholder card
            draw.rectangle([160, 240, 300, 380], fill=(0, 240, 255, 40), outline=(0, 240, 255, 120))
            draw.text((215, 300), "?", fill=(0, 240, 255, 200), font=self.fonts["title"])

        # Draw right Pokémon (facing left/down)
        sprite_right = self._load_sprite(t2_id, (sprite_w, sprite_h))
        if sprite_right:
            # We mirror the right Pokémon so it looks like it is facing the left one
            sprite_right = sprite_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            canvas.paste(sprite_right, (625, 210), sprite_right)
        else:
            draw.rectangle([660, 240, 800, 380], fill=(255, 105, 180, 40), outline=(255, 105, 180, 120))
            draw.text((715, 300), "?", fill=(255, 105, 180, 200), font=self.fonts["title"])

        # Draw weather overlay (covers the field and sprites)
        self._apply_weather_overlay(canvas, weather)

        # 3. Draw HUD Cards (glassmorphic overlays)
        self._draw_hud(draw, 40, 40, t1_poke, is_left=True)
        self._draw_hud(draw, 590, 40, t2_poke, is_left=False)

        # 4. Info Panel Overlay (turn, weather, etc.)
        info_w, info_h = 180, 72
        info_x = (width - info_w) // 2
        info_y = 20
        self._draw_glass_panel(draw, info_x, info_y, info_x + info_w, info_y + info_h)
        
        # Turn Text
        turn = getattr(battle, 'turn', 1)
        turn_text = f"TURN {turn}"
        tb = draw.textbbox((0, 0), turn_text, font=self.fonts["body_bold"])
        draw.text((info_x + (info_w - (tb[2] - tb[0])) // 2, info_y + 8), turn_text, fill=(255, 255, 255, 255), font=self.fonts["body_bold"])

        # Weather / Terrain Subtitles
        cond_text = f"☀ {weather.upper()}" if weather != "clear" else "☀ CLEAR"
        terr_text = f"⬡ {terrain.upper()}" if terrain != "normal" else "⬡ NORMAL"
        
        font_info = self.fonts["small_bold"]
        
        w_tb = draw.textbbox((0, 0), cond_text, font=font_info)
        draw.text((info_x + (info_w - (w_tb[2] - w_tb[0])) // 2, info_y + 32), cond_text, fill=(241, 196, 15, 220), font=font_info)
        
        t_tb = draw.textbbox((0, 0), terr_text, font=font_info)
        draw.text((info_x + (info_w - (t_tb[2] - t_tb[0])) // 2, info_y + 50), terr_text, fill=(46, 204, 113, 220), font=font_info)

        # Save buffer
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_team_preview(self, battle) -> io.BytesIO:
        """Generates a dynamic 2-row team preview interface showing both squads."""
        width, height = 760, 360
        canvas = self.asset_loader.get_background("team_preview_bg", width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # Draw a beautiful title banner
        self._draw_glass_panel(draw, 20, 15, width - 20, 50, border_color=(255, 255, 255, 60))
        title_text = f"TEAM PREVIEW: {battle.trainer1.name} vs {battle.trainer2.name}"
        font_title = self.fonts["body_bold"]
        title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
        draw.text(((width - (title_bbox[2] - title_bbox[0])) // 2, 23), title_text, fill=(255, 255, 255, 255), font=font_title)

        # Configuration for Pokemon list
        poke_w, poke_h = 88, 88
        col_gap = 18
        row1_y = 75
        row2_y = 210

        # Helper to draw a team row
        def draw_team_row(trainer, start_y, accent):
            party = trainer.party[:6]
            row_width = len(party) * poke_w + (len(party) - 1) * col_gap
            start_x = (width - row_width) // 2
            
            # Draw trainer label
            label = f"{trainer.name}'s squad:"
            draw.text((start_x, start_y - 20), label, fill=(255, 255, 255, 180), font=self.fonts["small_bold"])

            for idx, poke in enumerate(party):
                x = start_x + idx * (poke_w + col_gap)
                
                # Draw glass pocket frame
                self._draw_glass_panel(draw, x, start_y, x + poke_w, start_y + poke_h, border_color=accent)
                
                poke_id = getattr(poke, 'pokemon_id', getattr(poke, 'id', None))
                sprite = self._load_sprite(poke_id, (80, 80))
                if sprite:
                    canvas.paste(sprite, (int(x + 4), int(start_y + 4)), sprite)
                else:
                    draw.text((x + 38, start_y + 32), "?", fill=(255, 255, 255, 100), font=font_title)

                # Name badge below pocket
                name = poke._name.replace('-', ' ').title()
                if len(name) > 10:
                    name = name[:8] + ".."
                name_font = self.fonts["small"]
                nb = draw.textbbox((0, 0), name, font=name_font)
                nx = x + (poke_w - (nb[2] - nb[0])) // 2
                draw.text((nx, start_y + poke_h + 3), name, fill=(255, 255, 255, 230), font=name_font)

        # Draw Trainer 1 row (Cyan accent)
        draw_team_row(battle.trainer1, row1_y, (0, 240, 255, 120))
        # Draw Trainer 2 row (Pink accent)
        draw_team_row(battle.trainer2, row2_y, (255, 105, 180, 120))

        # Save buffer
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def _get_base_stats(self, identifier: str) -> dict[str, int]:
        """Look up base stats from static registries, falling back gracefully."""
        try:
            from ..core.registry import FORMS, POKEMON_STATS
            norm = identifier.lower().replace('-', '').replace(' ', '')
            form = None
            # pyrefly: ignore [missing-attribute]
            for k, f in FORMS.items():
                if k.lower().replace('-', '').replace(' ', '') == norm:
                    form = f
                    break
            if form:
                pid = form.get("pokemon_id") or form.get("id")
                stats_rec = POKEMON_STATS.get(pid)
                if stats_rec and "stats" in stats_rec:
                    stats = stats_rec["stats"]
                    return {
                        "hp": stats[0] if len(stats) > 0 else 50,
                        "atk": stats[1] if len(stats) > 1 else 50,
                        "def": stats[2] if len(stats) > 2 else 50,
                        "spa": stats[3] if len(stats) > 3 else 50,
                        "spd": stats[4] if len(stats) > 4 else 50,
                        "spe": stats[5] if len(stats) > 5 else 50,
                    }
        except Exception:
            pass
        return {"hp": 50, "atk": 50, "def": 50, "spa": 50, "spd": 50, "spe": 50}

    def render_pokemon_card(self, poke, player_name: str = "Trainer") -> io.BytesIO:
        """Generates a high-fidelity showcase card representing a single Pokémon."""
        width, height = 480, 280
        canvas = self.asset_loader.get_background("card_bg", width, height).copy()
        draw = ImageDraw.Draw(canvas)

        # Main glass frame
        self._draw_glass_panel(draw, 15, 15, width - 15, height - 15, border_color=(255, 255, 255, 50))

        # Extract values depending on whether input is dict or object
        from ..core.registry import FORMS, POKE_ABILITIES, ABILITIES
        if isinstance(poke, dict):
            # Resolve pokemon_id from FORMS name
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
            
            # Resolve ability dynamically from ability_index
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
            
            ivs = {
                "hp": poke.get("hpiv", 31),
                "atk": poke.get("atkiv", 31),
                "def": poke.get("defiv", 31),
                "spa": poke.get("spatkiv", 31),
                "spd": poke.get("spdefiv", 31),
                "spe": poke.get("speediv", 31)
            }
            evs = {
                "hp": poke.get("hpev", 0),
                "atk": poke.get("atkev", 0),
                "def": poke.get("defev", 0),
                "spa": poke.get("spatkev", 0),
                "spd": poke.get("spdefev", 0),
                "spe": poke.get("speedev", 0)
            }
            moves = poke.get("moves", [])
        else:
            # Resolve pokemon_id from FORMS name
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
            
            # Resolve ability dynamically from ability_index
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
            
            base_stats = getattr(poke, 'base_stats', {})
            # Handle object with stats-by-name dict
            raw_name = getattr(poke, '_name', '').lower()
            if raw_name in base_stats:
                bs_raw = base_stats[raw_name]
            elif name_text.lower() in base_stats:
                bs_raw = base_stats[name_text.lower()]
            else:
                bs_raw = base_stats
                
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

            ivs = {
                "hp": getattr(poke, "hpiv", 31),
                "atk": getattr(poke, "atkiv", 31),
                "def": getattr(poke, "defiv", 31),
                "spa": getattr(poke, "spatkiv", 31),
                "spd": getattr(poke, "spdefiv", 31),
                "spe": getattr(poke, "speediv", 31)
            }
            evs = {
                "hp": getattr(poke, "hpev", 0),
                "atk": getattr(poke, "atkev", 0),
                "def": getattr(poke, "defev", 0),
                "spa": getattr(poke, "spatkev", 0),
                "spd": getattr(poke, "spdefev", 0),
                "spe": getattr(poke, "speedev", 0)
            }
            moves = getattr(poke, 'moves', [])

        # Sprite Box
        self._draw_glass_panel(draw, 30, 30, 180, 180, border_color=(0, 240, 255, 100))
        sprite = self._load_sprite(poke_id, (140, 140))
        if sprite:
            canvas.paste(sprite, (35, 35), sprite)
        else:
            draw.text((95, 95), "?", fill=(255, 255, 255, 120), font=self.fonts["title"])

        # Pokemon stats text layout
        draw.text((200, 32), display_name, fill=(255, 255, 255, 255), font=self.fonts["title"])
        
        if not item_val or item_val == "None":
            item_val = "No Item"
            
        nature_text = f"Nature: {str(nature_val).title()}"
        ability_text = f"Ability: {str(ability_val).replace('-', ' ').title()}"
        item_text = f"Held: {str(item_val).replace('-', ' ').title()}"
        
        draw.text((200, 64), nature_text, fill=(180, 200, 220, 255), font=self.fonts["body"])
        draw.text((200, 84), ability_text, fill=(180, 200, 220, 255), font=self.fonts["body"])
        draw.text((200, 104), item_text, fill=(180, 200, 220, 255), font=self.fonts["body"])

        # Stats Table (IVs / EVs)
        stat_y = 135
        draw.text((200, stat_y), "STAT   BASE   IV   EV", fill=(0, 240, 255, 200), font=self.fonts["small_bold"])
        
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP ", "ATK", "DEF", "SPA", "SPD", "SPE"]
        
        for idx, key in enumerate(stats_keys):
            y_offset = stat_y + 16 + (idx * 16)
            lbl = stats_labels[idx]
            
            bs_v = base_stats.get(key, 0)
            iv_v = ivs.get(key, 31)
            ev_v = evs.get(key, 0)
            
            stat_row = f"{lbl:<6} {bs_v:<6} {iv_v:<4} {ev_v:<4}"
            draw.text((200, y_offset), stat_row, fill=(240, 244, 255, 240), font=self.fonts["small"])

        # Moveset layout (in bottom-left quadrant below sprite)
        moves_y = 195
        draw.text((30, moves_y), "MOVESET:", fill=(0, 240, 255, 200), font=self.fonts["small_bold"])
        
        for idx, move in enumerate(moves[:4]):
            m_y = moves_y + 14 + (idx * 14)
            m_name = move.replace('-', ' ').title() if move else "-"
            draw.text((34, m_y), f"• {m_name}", fill=(240, 244, 255, 220), font=self.fonts["small"])

        # Save buffer
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
