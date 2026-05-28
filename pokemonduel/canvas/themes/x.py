import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class XRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        # Light blue gradient background
        canvas = Image.new("RGBA", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        # Draw soft gradient top to bottom
        for y in range(height):
            f = y / height
            r = int(240 * (1 - f) + 220 * f)
            g = int(248 * (1 - f) + 235 * f)
            b = int(255 * (1 - f) + 250 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Thin soft frame
        draw.rectangle([0, 0, width - 1, height - 1], outline=(96, 144, 192), width=2)

        # 1. Soft Blue Header
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="KALOS TRAINER PASSPORT", bg=(96, 144, 192))

        # 2. Left Details Panel with soft blue header bands
        self.renderer._draw_classic_panel(draw, 14, 48, 320, 188, fill=(255, 255, 255), border=(160, 192, 224), radius=6)
        
        draw.text((24, 56), "NAME:", fill=(96, 144, 192), font=self.fonts["small_bold"])
        draw.text((70, 54), username, fill=self.palette.text_dark, font=self.fonts["body_bold"])
        
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((200, 56), f"IDNo. {id_no}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Soft blue details
        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("BATTLES RECORD", f"{wins}W / {losses}L"),
            ("ACTIVE TEAM", f"{active_team}"),
        ]

        dy = 84
        for label, val in info_items:
            # Draw tiny band
            draw.rectangle([20, dy - 2, 110, dy + 16], fill=(230, 240, 250), outline=(208, 224, 240))
            draw.text((24, dy), label, fill=(96, 144, 192), font=self.fonts["tiny"])
            
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((310 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 24

        # 3. Avatar Panel
        self.renderer._draw_classic_panel(draw, 334, 48, 466, 188, fill=(255, 255, 255), border=(160, 192, 224), radius=6)
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((128, 136), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (336, 50), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 400, 118
            r = 30
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 248, 255), outline=(160, 192, 224), width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=(160, 192, 224), width=2)

        # 4. Active Team Section (Glabrous rounded slots)
        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(240, 248, 255), border=(160, 192, 224), radius=6)

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(255, 255, 255), border=(180, 208, 240), border_width=1, radius=4)

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
                cx, cy = sx + 28, sy + 28
                draw.text((cx - 4, cy - 8), "?", fill=(180, 192, 208), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer", 
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        # Gradient background
        canvas = Image.new("RGBA", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        for y in range(height):
            f = y / height
            r = int(240 * (1 - f) + 215 * f)
            g = int(248 * (1 - f) + 230 * f)
            b = int(255 * (1 - f) + 248 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        draw.rectangle([0, 0, width - 1, height - 1], outline=(96, 144, 192), width=2)

        # 1. Left Summary Panel (Rounded with soft shadow)
        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(255, 255, 255), border=(160, 192, 224), radius=8)
        
        # Name banner
        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(96, 144, 192))
        
        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        # OT / Nature / Held Item
        draw.text((20, 170), f"OT: {player_name.upper()}", fill=(120, 140, 160), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((20, 198), f"ITEM: {str(data['item']).replace('-', ' ').upper()}", fill=(120, 140, 160), font=self.fonts["tiny"])

        # Type badges
        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        # 2. Right Stats Panel (Rounded, modern bar charts)
        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 255, 255), border=(160, 192, 224), radius=8)
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="POKéMON SKILLS", bg=(96, 144, 192))

        draw.text((200, 48), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(120, 140, 160), font=self.fonts["small_bold"])

        # Stats Table
        stats_y = 86
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP", "ATK", "DEF", "SpA", "SpD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + (idx * 24)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            # Draw Label
            draw.text((200, y_offset), lbl, fill=(96, 144, 192), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small"])

            # Modern smooth rounded bar
            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))
            
            # Empty container
            draw.rounded_rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], radius=3, fill=(240, 245, 250), outline=(208, 224, 240))
            # Fill bar (Blue)
            draw.rounded_rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], radius=3, fill=(96, 144, 192))

            draw.text((380, y_offset), f"IV {iv_v}", fill=(160, 170, 180), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(200, 160, 80), font=self.fonts["tiny"])

        # Moves Footer
        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(240, 248, 255), border=(160, 192, 224), border_width=1, radius=4)
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
            canvas_bg=(240, 248, 255),
            header_bg=(96, 144, 192),
            panel_bg=(255, 255, 255),
            panel_border=(96, 144, 192),
            row_alt_bg=(240, 248, 255),
            text_color=self.palette.text_dark,
            text_secondary=(80, 112, 144),
            accent_color=(96, 144, 192),
            border_radius=6,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        for y in range(height):
            f = y / height
            r = int(240 * (1 - f) + 220 * f)
            g = int(248 * (1 - f) + 235 * f)
            b = int(255 * (1 - f) + 250 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        draw.rectangle([0, 0, width - 1, height - 1], outline=(96, 144, 192), width=3)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="3DS SYSTEM PREFERENCES", bg=(96, 144, 192))

        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=(255, 255, 255), border=(160, 192, 224), radius=8)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        # Option 1: Theme App
        card_x, card_y = 30, 68
        self.renderer._draw_classic_panel(draw, card_x, card_y, card_x + 120, card_y + 40, fill=(240, 248, 255), border=(96, 144, 192), radius=6)
        draw.text((card_x + 14, card_y + 10), "THEME APP", fill=(96, 144, 192), font=self.fonts["small_bold"])

        val_x = 170
        self.renderer._draw_classic_panel(draw, val_x, card_y, val_x + 270, card_y + 40, fill=(255, 255, 255), border=(160, 192, 224), radius=6)
        draw.text((val_x + 24, card_y + 10), current_theme.upper(), fill=self.palette.text_dark, font=font)

        # Option 2: Moveset Display App
        card_y2 = 124
        self.renderer._draw_classic_panel(draw, card_x, card_y2, card_x + 120, card_y2 + 40, fill=(240, 248, 255), border=(96, 144, 192), radius=6)
        draw.text((card_x + 6, card_y2 + 10), "MOVESET DISP", fill=(96, 144, 192), font=self.fonts["small_bold"])

        moveset_val = "IMAGE" if moveset_img else "TEXT"
        self.renderer._draw_classic_panel(draw, val_x, card_y2, val_x + 270, card_y2 + 40, fill=(255, 255, 255), border=(160, 192, 224), radius=6)
        draw.text((val_x + 24, card_y2 + 10), moveset_val, fill=self.palette.text_dark, font=font)

        help_txt = "Press dropdown select to swap app configurations."
        draw.text((24, 220), help_txt, fill=(120, 140, 160), font=font_sm)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

