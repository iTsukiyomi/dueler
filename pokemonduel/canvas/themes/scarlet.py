import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class ScarletRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        # Scarlet Naranja Academy theme colors
        canvas = Image.new("RGBA", (width, height), (255, 245, 245))
        draw = ImageDraw.Draw(canvas)

        # Phone App Border
        draw.rectangle([0, 0, width - 1, height - 1], outline=(220, 40, 60), width=4)
        draw.rectangle([4, 4, width - 5, height - 5], outline=(255, 255, 255), width=1)

        # 1. Rotom App Bar (top status bar)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="ROTOM PROFILE APP", bg=(220, 40, 60))

        # 2. Left Column: Smartphone App Stats Cards
        self.renderer._draw_classic_panel(draw, 14, 48, 300, 188, fill=(255, 255, 255), border=(245, 220, 220), radius=8)
        
        draw.text((24, 56), "APP USER:", fill=(160, 64, 80), font=self.fonts["small_bold"])
        draw.text((86, 54), username.upper(), fill=self.palette.text_dark, font=self.fonts["body_bold"])
        
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((200, 56), f"IDNo. {id_no}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Thin divider
        draw.line([(20, 76), (290, 76)], fill=(245, 220, 220), width=1)

        info_items = [
            ("BALANCE (¥)", f"¥{wallet:,}"),
            ("ACADEMY ELO", f"{elo}"),
            ("WINS / LOSSES", f"{wins}W / {losses}L"),
            ("ROTOM PHONE ID", f"{active_team.upper()}"),
        ]

        dy = 84
        for label, val in info_items:
            # Draw smartphone circular bullet point
            draw.ellipse([24, dy + 2, 30, dy + 8], fill=(220, 40, 60))
            draw.text((36, dy), label, fill=(160, 64, 80), font=self.fonts["tiny"])
            
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((288 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 22

        # 3. Avatar Panel: Smartphone Circular Crop Pic!
        self.renderer._draw_classic_panel(draw, 314, 48, 466, 188, fill=(255, 255, 255), border=(220, 40, 60), radius=8)
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                # Circular crop avatar
                avatar_img = avatar_img.resize((136, 134), Image.Resampling.LANCZOS)
                
                # Mask to create circular profile pic
                mask = Image.new("L", (136, 134), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, 136, 134], fill=255)
                
                output_avatar = Image.new("RGBA", (136, 134), (0, 0, 0, 0))
                output_avatar.paste(avatar_img, (0, 0), mask)
                
                canvas.paste(output_avatar, (322, 51), output_avatar)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 390, 118
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 245, 245), outline=(220, 40, 60), width=2)
            draw.text((cx - 10, cy - 10), "SV", fill=(220, 40, 60), font=self.fonts["small_bold"])

        # 4. Active Team Section (6 circular app slots)
        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(255, 255, 255), border=(220, 40, 60), radius=8)

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            # Circular app slot border
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(255, 245, 245), border=(220, 40, 60), border_width=1, radius=28)

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
                # Mask sprite to circular boundaries
                mask = Image.new("L", (48, 48), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, 48, 48], fill=255)
                output_sprite = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
                output_sprite.paste(sprite, (0, 0), mask)
                canvas.paste(output_sprite, (sx + 4, sy + 4), output_sprite)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer", 
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        # Scarlet Naranja App summary background
        canvas = Image.new("RGBA", (width, height), (255, 245, 245))
        draw = ImageDraw.Draw(canvas)

        # Phone border
        draw.rectangle([0, 0, width - 1, height - 1], outline=(220, 40, 60), width=3)

        # 1. Left Summary App Pane
        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(255, 255, 255), border=(220, 40, 60), radius=8)
        
        # Name block
        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(220, 40, 60))
        
        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        # Nature and OT details
        draw.text((20, 170), f"TRAINER: {player_name.upper()}", fill=(160, 64, 80), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Type badges (Rotom App chip pill badge style)
        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        # 2. Right Stats Panel (Smartphone app grid layout with scarlet trims)
        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 255, 255), border=(220, 40, 60), radius=8)
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="ROTOM SUMMARY APP", bg=(220, 40, 60))

        # Prominent Tera type indicator (SV unique feature!)
        draw.text((200, 46), "TERA TYPE: STELLAR", fill=(220, 40, 60), font=self.fonts["tiny"])
        draw.text((200, 58), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(160, 64, 80), font=self.fonts["small_bold"])

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
            draw.text((200, y_offset), lbl, fill=(220, 40, 60), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small"])

            # Rotom Phone bar chart
            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))
            
            # Empty container
            draw.rounded_rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], radius=4, fill=(255, 245, 245), outline=(245, 220, 220))
            # Fill bar (Scarlet Red)
            draw.rounded_rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], radius=4, fill=(220, 40, 60))

            draw.text((380, y_offset), f"IV {iv_v}", fill=(180, 160, 160), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(220, 120, 120), font=self.fonts["tiny"])

        # Moves Footer
        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(255, 245, 245), border=(220, 40, 60), border_width=1, radius=6)
        move_names = []
        for move in data["moves"][:3]:
            name = move.replace('-', ' ').upper() if isinstance(move, str) else getattr(move, 'pretty_name', str(move)).upper()
            move_names.append(name)
        draw.text((202, moves_y + 4), "MOVES: " + " │ ".join(move_names), fill=self.palette.text_dark, font=self.fonts["tiny"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_settings_menu(self, current_theme: str) -> io.BytesIO:
        width, height = 480, 240
        canvas = Image.new("RGBA", (width, height), (255, 245, 245))
        draw = ImageDraw.Draw(canvas)

        # Phone App Border
        draw.rectangle([0, 0, width - 1, height - 1], outline=(220, 40, 60), width=4)

        # Rotom settings status bar
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="ROTOM SETTINGS APP", bg=(220, 40, 60))

        # Main smartphone grid layout (app tiles)
        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=(255, 255, 255), border=(245, 220, 220), radius=8)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        # Option Tile 1 (UI THEME App Tile)
        tile_x, tile_y = 30, 68
        self.renderer._draw_classic_panel(draw, tile_x, tile_y, tile_x + 120, tile_y + 80, fill=(255, 245, 245), border=(220, 40, 60), radius=8)
        
        # Rotom face graphic simulated on tile
        draw.ellipse([tile_x + 40, tile_y + 15, tile_x + 80, tile_y + 35], fill=(220, 40, 60))
        draw.text((tile_x + 22, tile_y + 50), "THEME CONG", fill=(160, 64, 80), font=self.fonts["tiny"])

        # Display Selected Theme (smartphone crop display)
        val_x, val_y = 170, 68
        self.renderer._draw_classic_panel(draw, val_x, val_y, val_x + 270, val_y + 80, fill=(255, 255, 255), border=(220, 40, 60), radius=8)
        draw.text((val_x + 24, val_y + 30), current_theme.upper(), fill=self.palette.text_dark, font=font)

        # Help Footer text
        help_txt = "Rotom: Swipe option dropdown selection below to save changes."
        draw.text((24, 180), help_txt, fill=(160, 64, 80), font=font_sm)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
