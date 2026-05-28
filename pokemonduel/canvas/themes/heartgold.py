import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class HeartGoldRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        # Create gold cream DS styled background
        canvas = Image.new("RGBA", (width, height), (250, 245, 230))
        draw = ImageDraw.Draw(canvas)

        # Gold trimming borders
        draw.rectangle([0, 0, width - 1, height - 1], outline=(200, 160, 80), width=4)
        draw.rectangle([4, 4, width - 5, height - 5], outline=(255, 255, 255), width=2)

        # 1. Title Bar
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="JOHTO TRAINER CASE", bg=(200, 160, 80))

        # 2. Left Column: Details (Johto parchment feel)
        self.renderer._draw_classic_panel(draw, 14, 48, 300, 188, fill=(255, 253, 245), border=(200, 160, 80))
        draw.text((24, 56), "NAME:", fill=(140, 110, 50), font=self.fonts["small_bold"])
        draw.text((70, 54), username, fill=self.palette.text_dark, font=self.fonts["body_bold"])
        
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((180, 56), f"IDNo. {id_no}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        draw.line([(20, 76), (290, 76)], fill=(220, 200, 160), width=1)

        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("RECORD", f"{wins}W / {losses}L"),
            ("ACTIVE TEAM", f"{active_team}"),
        ]

        dy = 84
        for label, val in info_items:
            draw.text((24, dy), label, fill=(140, 110, 50), font=self.fonts["small_bold"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((288 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 22

        # 3. Avatar Frame (rounded)
        self.renderer._draw_classic_panel(draw, 314, 48, 466, 150, fill=(245, 240, 225), border=(200, 160, 80))
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((146, 96), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (317, 51), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            # Gold outline Pokéball
            cx, cy = 390, 99
            r = 30
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=(200, 160, 80), width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=(200, 160, 80), width=2)
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(250, 245, 230), outline=(200, 160, 80), width=2)

        # 4. Drawing/Signature Box (Bottom Right)
        self.renderer._draw_classic_panel(draw, 314, 156, 466, 188, fill=(255, 255, 255), border=(220, 200, 160), radius=2)
        draw.text((320, 158), "SIGNATURE", fill=(180, 160, 120), font=self.fonts["tiny"])
        # Draw dynamic signature scribble
        draw.line([(340, 178), (350, 168), (365, 180), (380, 165), (410, 175), (440, 162)], fill=(40, 80, 160), width=2)

        # 5. Badges/Stamps Section (Bottom row: 6 Golden Stamp boxes showing team)
        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(245, 240, 225), border=(200, 160, 80))

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            # Golden slot border
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(255, 253, 245), border=(200, 160, 80), border_width=1, radius=3)

            poke_id = None
            poke_name = None
            if party_pokemon and idx < len(party_pokemon):
                poke = party_pokemon[idx]
                pokname = poke.get("pokname", "")
                if pokname:
                    poke_name = pokname
                    form_info = FORMS.get(pokname.lower())
                    if form_info:
                        poke_id = form_info.get("pokemon_id")

            sprite = None
            if poke_id:
                sprite = self.renderer._load_sprite(poke_id, (48, 48), name=poke_name)

            if sprite:
                canvas.paste(sprite, (sx + 4, sy + 4), sprite)
            else:
                # Golden star symbol placeholder
                cx, cy = sx + 28, sy + 28
                draw.text((cx - 8, cy - 8), "★", fill=(220, 180, 100), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer", 
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        # Warm gold DS cream summary background
        canvas = Image.new("RGBA", (width, height), (250, 248, 240))
        draw = ImageDraw.Draw(canvas)

        # Gold Trim
        draw.rectangle([0, 0, width - 1, height - 1], outline=(200, 160, 80), width=3)

        # 1. Left Panel (Designed like DS Top Screen summary)
        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(255, 253, 245), border=(200, 160, 80))
        
        # Name block
        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(200, 160, 80))
        
        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)
            
        # Level indicator / Held item info
        draw.text((20, 170), "HELD ITEM:", fill=(140, 110, 50), font=self.fonts["tiny"])
        draw.text((20, 184), str(data["item"]).replace('-', ' ').upper(), fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Type badges inside Left Panel
        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        # 2. Right Panel (DS Bottom Screen Tab content)
        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 255, 255), border=(200, 160, 80))

        # Labeled Tab headers
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="POKéMON SKILLS", bg=(180, 140, 60))

        # Nature and Ability Details
        draw.text((200, 48), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((200, 64), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(140, 110, 50), font=self.fonts["small_bold"])

        # Stats Table with bars
        stats_y = 90
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP", "ATK", "DEF", "SpA", "SpD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + (idx * 24)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            # Draw Label
            draw.text((200, y_offset), lbl, fill=(100, 80, 40), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small"])

            # Render stat bar charts inside right panel (Gen 4 DS style)
            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))
            
            # Draw empty bar container
            draw.rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], fill=(240, 235, 225), outline=(200, 190, 170))
            # Fill bar
            draw.rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], fill=(220, 180, 60))

            # IV / EV info details
            draw.text((380, y_offset), f"IV {iv_v}", fill=(120, 120, 120), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(200, 140, 60), font=self.fonts["tiny"])

        # Moves footer list
        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(250, 248, 240), border=(200, 160, 80), border_width=1, radius=2)
        
        move_names = []
        for move in data["moves"][:4]:
            name = move.replace('-', ' ').upper() if isinstance(move, str) else getattr(move, 'pretty_name', str(move)).upper()
            move_names.append(name)
        
        draw.text((202, moves_y + 4), "MOVES: " + " │ ".join(move_names), fill=self.palette.text_dark, font=self.fonts["tiny"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_moveset(self, pokemon_name: str, moves_data: list[dict],
                       page: int, total_pages: int, total_moves: int) -> io.BytesIO:
        return self._render_moveset_table(
            pokemon_name, moves_data, page, total_pages, total_moves,
            canvas_bg=(250, 248, 240),
            header_bg=(200, 160, 80),
            panel_bg=(255, 253, 245),
            panel_border=(200, 160, 80),
            row_alt_bg=(245, 240, 225),
            text_color=self.palette.text_dark,
            text_secondary=(140, 110, 50),
            accent_color=(220, 180, 60),
            border_radius=4,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (250, 245, 230))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(200, 160, 80), width=4)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="SETTINGS APP", bg=(200, 160, 80))

        self.renderer._draw_classic_panel(draw, 14, 50, width - 14, height - 12, fill=(255, 253, 245), border=(220, 200, 160))

        grid_w, grid_h = 138, 48

        # Row 1: UI THEME
        rx, ry = 30, 68
        self.renderer._draw_classic_panel(draw, rx, ry, rx + grid_w, ry + grid_h, fill=(200, 160, 80), border=(160, 120, 50), radius=4)
        draw.text((rx + 16, ry + 16), "ACTIVE THEME", fill=(255, 255, 255), font=self.fonts["small_bold"])

        tx, ty = 188, 68
        self.renderer._draw_classic_panel(draw, tx, ty, tx + 248, ty + grid_h, fill=(255, 255, 255), border=(200, 160, 80), radius=4)
        draw.text((tx + 24, ty + 16), current_theme.upper(), fill=self.palette.text_dark, font=self.fonts["body_bold"])

        # Row 2: MOVESET DISPLAY
        rx2, ry2 = 30, 128
        self.renderer._draw_classic_panel(draw, rx2, ry2, rx2 + grid_w, ry2 + grid_h, fill=(200, 160, 80), border=(160, 120, 50), radius=4)
        draw.text((rx2 + 10, ry2 + 16), "MOVESET DISPLAY", fill=(255, 255, 255), font=self.fonts["small_bold"])

        tx2, ty2 = 188, 128
        moveset_val = "IMAGE" if moveset_img else "TEXT"
        self.renderer._draw_classic_panel(draw, tx2, ty2, tx2 + 248, ty2 + grid_h, fill=(255, 255, 255), border=(200, 160, 80), radius=4)
        draw.text((tx2 + 24, ty2 + 16), moveset_val, fill=self.palette.text_dark, font=self.fonts["body_bold"])

        help_txt = "Tap options dropdown to modify."
        draw.text((32, 228), help_txt, fill=(160, 140, 110), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

