import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class SunRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        # Warm sand yellow passport page base
        canvas = Image.new("RGBA", (width, height), (255, 250, 230))
        draw = ImageDraw.Draw(canvas)

        # Tropical borders (Kapa Hawaiian patterns simulated with dotted outlines)
        draw.rectangle([0, 0, width - 1, height - 1], outline=(248, 160, 72), width=3)
        draw.rectangle([4, 4, width - 5, height - 5], outline=(255, 230, 180), width=1)

        # 1. Passport Title
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="ALOLA PASSPORT BOOKLET", bg=(248, 160, 72))

        # 2. Passport Photo Frame (Left Column)
        photo_x, photo_y = 14, 48
        self.renderer._draw_classic_panel(draw, photo_x, photo_y, photo_x + 140, photo_y + 140, fill=(255, 255, 255), border=(248, 160, 72), radius=4)
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((136, 136), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (photo_x + 2, photo_y + 2), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            # Tropical outline symbol
            cx, cy = photo_x + 70, photo_y + 70
            draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(255, 250, 230), outline=(248, 160, 72), width=2)
            draw.text((cx - 10, cy - 10), "☀", fill=(248, 160, 72), font=self.fonts["body_bold"])

        # 3. Passport Text Details (Right Column)
        info_x = 166
        self.renderer._draw_classic_panel(draw, info_x, 48, 466, 188, fill=(255, 253, 245), border=(248, 160, 72), radius=4)

        draw.text((info_x + 12, 56), "PASSPORT NAME:", fill=(160, 112, 72), font=self.fonts["tiny"])
        draw.text((info_x + 12, 68), username.upper(), fill=self.palette.text_dark, font=self.fonts["body_bold"])
        
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((370, 56), f"No. {id_no}", fill=(160, 112, 72), font=self.fonts["tiny"])

        draw.line([(info_x + 12, 88), (454, 88)], fill=(248, 230, 200), width=1)

        info_items = [
            ("ALOLA ELO", f"{elo}"),
            ("WALLET", f"¥{wallet:,}"),
            ("RECORD STATS", f"{wins}W / {losses}L"),
            ("TEAM ID", f"{active_team.upper()}"),
        ]

        dy = 96
        for label, val in info_items:
            draw.text((info_x + 12, dy), label, fill=(160, 112, 72), font=self.fonts["tiny"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((454 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 22

        # 4. Island Challenge Stamps (Bottom grid displaying active team as stamps)
        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(255, 255, 255), border=(248, 160, 72), radius=6)

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            # Stamp frame border (wavy dash outline style)
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(255, 250, 240), border=(255, 180, 120), border_width=1, radius=6)

            # Draw a tiny passport stamp serrated crop
            draw.rectangle([sx + 3, sy + 3, sx + slot_w - 3, sy + slot_h - 3], outline=(248, 160, 72), width=1)

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
                # Stamp sun icon placeholder
                cx, cy = sx + 28, sy + 28
                draw.text((cx - 8, cy - 8), "☀", fill=(255, 210, 140), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer", 
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        # Warm sandy yellow summary background
        canvas = Image.new("RGBA", (width, height), (255, 250, 230))
        draw = ImageDraw.Draw(canvas)

        # Tropical frame
        draw.rectangle([0, 0, width - 1, height - 1], outline=(248, 160, 72), width=2)

        # 1. Left Panel (Alola touch screen style summary)
        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(255, 255, 255), border=(248, 160, 72), radius=6)
        
        # Name block
        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(248, 160, 72))
        
        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        # OT / Nature / Held Item
        draw.text((20, 170), f"OT: {player_name.upper()}", fill=(160, 112, 72), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((20, 198), f"ITEM: {str(data['item']).replace('-', ' ').upper()}", fill=(160, 112, 72), font=self.fonts["tiny"])

        # Type badges
        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        # 2. Right Panel (Tropical floral details page)
        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 253, 245), border=(248, 160, 72), radius=6)
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="ALOLA REGISTRY", bg=(248, 160, 72))

        draw.text((200, 48), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(160, 112, 72), font=self.fonts["small_bold"])

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
            draw.text((200, y_offset), lbl, fill=(248, 160, 72), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small"])

            # Sand yellow progress bars
            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))
            
            # Empty container
            draw.rounded_rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], radius=3, fill=(255, 250, 230), outline=(248, 230, 210))
            # Fill bar
            draw.rounded_rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], radius=3, fill=(248, 160, 72))

            draw.text((380, y_offset), f"IV {iv_v}", fill=(160, 150, 130), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(200, 160, 80), font=self.fonts["tiny"])

        # Moves Footer
        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(255, 255, 255), border=(248, 160, 72), border_width=1, radius=4)
        move_names = []
        for move in data["moves"][:4]:
            name = move.replace('-', ' ').upper() if isinstance(move, str) else getattr(move, 'pretty_name', str(move)).upper()
            move_names.append(name)
        draw.text((202, moves_y + 4), "MOVES: " + " │ ".join(move_names), fill=self.palette.text_dark, font=self.fonts["tiny"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_settings_menu(self, current_theme: str) -> io.BytesIO:
        width, height = 480, 240
        canvas = Image.new("RGBA", (width, height), (255, 250, 230))
        draw = ImageDraw.Draw(canvas)

        # Tropical borders
        draw.rectangle([0, 0, width - 1, height - 1], outline=(248, 160, 72), width=3)

        # Top screen header display style
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="ROTOM PHONE SETTINGS", bg=(248, 160, 72))

        # Bottom touchscreen layout
        self.renderer._draw_classic_panel(draw, 14, 50, width - 14, height - 12, fill=(255, 255, 255), border=(248, 160, 72), radius=6)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        # Option selection block
        grid_w, grid_h = 138, 48
        rx, ry = 30, 68
        self.renderer._draw_classic_panel(draw, rx, ry, rx + grid_w, ry + grid_h, fill=(248, 160, 72), border=(220, 130, 40), radius=4)
        draw.text((rx + 16, ry + 16), "ACTIVE THEME", fill=(255, 255, 255), font=self.fonts["small_bold"])

        # Display Selected Theme
        tx, ty = 188, 68
        self.renderer._draw_classic_panel(draw, tx, ty, tx + 248, ty + grid_h, fill=(255, 250, 240), border=(248, 160, 72), radius=4)
        draw.text((tx + 24, ty + 16), current_theme.upper(), fill=self.palette.text_dark, font=font)

        # Help hint
        help_txt = "Rotom: Tap below option dropdown to config Alola settings!"
        draw.text((32, 178), help_txt, fill=(160, 112, 72), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
