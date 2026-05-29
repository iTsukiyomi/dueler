import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class SwordRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 300, 480
        canvas = Image.new("RGBA", (width, height), (250, 252, 255))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(32, 96, 192), width=4)

        draw.rectangle([4, 4, width - 5, 40], fill=(32, 96, 192))
        draw.text((14, 12), "GALAR LEAGUE CARD", fill=(255, 255, 255), font=self.fonts["small_bold"])

        self.renderer._draw_classic_panel(draw, 14, 52, 286, 252, fill=(240, 245, 250), border=(32, 96, 192), radius=6)
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                # Scale to fill the box.
                avatar_img = avatar_img.resize((268, 196), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (16, 54), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 150, 152
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 255, 255), outline=(32, 96, 192), width=2)
            draw.text((cx - 14, cy - 10), "SwSh", fill=(32, 96, 192), font=self.fonts["small_bold"])

        draw.text((20, 226), "★ 7 STAR", fill=(255, 203, 5), font=self.fonts["small_bold"])
        draw.text((230, 226), "#999", fill=(255, 255, 255), font=self.fonts["body_bold"])

        self.renderer._draw_classic_panel(draw, 14, 264, 286, 396, fill=(255, 255, 255), border=(224, 235, 250), radius=6)

        draw.text((24, 274), f"TRAINER: {username.upper()}", fill=(32, 96, 192), font=self.fonts["small_bold"])

        info_items = [
            ("WALLET", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("LEAGUE RECORD", f"{wins}W / {losses}L"),
            ("ACTIVE TEAM", f"{active_team.upper()}"),
        ]

        dy = 296
        for label, val in info_items:
            draw.text((24, dy), label, fill=(64, 96, 144), font=self.fonts["tiny"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((276 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 22

        self.renderer._draw_classic_panel(draw, 14, 408, 286, 466, fill=(240, 245, 250), border=(32, 96, 192), radius=6)

        slot_w, slot_h = 36, 36
        gap = 6
        sx_start = 24
        sy = 416

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(255, 255, 255), border=(32, 96, 192), border_width=1, radius=2)

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
                sprite = self.renderer._load_sprite(poke_id, (32, 32), name=poke_name)

            if sprite:
                canvas.paste(sprite, (sx + 2, sy + 2), sprite)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer",
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        canvas = Image.new("RGBA", (width, height), (250, 252, 255))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(32, 96, 192), width=3)

        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(255, 255, 255), border=(32, 96, 192), radius=6)

        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(32, 96, 192))

        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        draw.text((20, 170), f"TRAINER: {player_name.upper()}", fill=(64, 96, 144), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((20, 198), f"ITEM: {str(data['item']).replace('-', ' ').upper()}", fill=(64, 96, 144), font=self.fonts["tiny"])

        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 255, 255), border=(32, 96, 192), radius=6)
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="GALAR SUMMARY", bg=(32, 96, 192))

        draw.text((200, 48), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(64, 96, 144), font=self.fonts["small_bold"])

        stats_y = 86
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP", "ATK", "DEF", "SpA", "SpD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + (idx * 24)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            draw.text((200, y_offset), lbl, fill=(32, 96, 192), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small"])

            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))

            draw.rounded_rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], radius=4, fill=(240, 245, 250), outline=(224, 235, 250))
            draw.rounded_rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], radius=4, fill=(32, 96, 192))

            draw.text((380, y_offset), f"IV {iv_v}", fill=(120, 140, 160), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(200, 160, 80), font=self.fonts["tiny"])

        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(240, 245, 250), border=(32, 96, 192), border_width=1, radius=4)
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
            canvas_bg=(250, 252, 255),
            header_bg=(32, 96, 192),
            panel_bg=(255, 255, 255),
            panel_border=(32, 96, 192),
            row_alt_bg=(240, 245, 250),
            text_color=self.palette.text_dark,
            text_secondary=(64, 96, 144),
            accent_color=(32, 96, 192),
            border_radius=6,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True,
                              help_display: str = "image") -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (250, 252, 255))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(32, 96, 192), width=3)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="SWITCH PREFERENCES", bg=(32, 96, 192))

        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=(255, 255, 255), border=(224, 235, 250), radius=6)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        draw.text((36, 68), "SYSTEM THEME", fill=(64, 96, 144), font=font)
        self.renderer._draw_classic_panel(draw, 220, 62, 440, 88, fill=(32, 96, 192), border=(16, 48, 96), radius=4)
        draw.text((236, 66), current_theme.upper() + "  ›", fill=(255, 255, 255), font=font)

        draw.text((36, 104), "MOVESET DISPLAY", fill=(64, 96, 144), font=font)
        moveset_val = "IMAGE  ›" if moveset_img else "TEXT  ›"
        self.renderer._draw_classic_panel(draw, 220, 98, 440, 124, fill=(32, 96, 192), border=(16, 48, 96), radius=4)
        draw.text((236, 102), moveset_val, fill=(255, 255, 255), font=font)

        draw.text((36, 140), "HELP DISPLAY", fill=(64, 96, 144), font=font)
        help_val = help_display.upper() + "  ›"
        self.renderer._draw_classic_panel(draw, 220, 134, 440, 160, fill=(32, 96, 192), border=(16, 48, 96), radius=4)
        draw.text((236, 138), help_val, fill=(255, 255, 255), font=font)

        help_txt = "Press option dropdown selection below to change."
        draw.text((36, 220), help_txt, fill=(120, 140, 160), font=font_sm)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_help_page(self, category: str, commands_list: list[dict],
                         page: int, total_pages: int) -> io.BytesIO:
        return self._render_help_table(
            category, commands_list, page, total_pages,
            canvas_bg=(250, 252, 255),
            header_bg=(32, 96, 192),
            panel_bg=(255, 255, 255),
            panel_border=(32, 96, 192),
            row_alt_bg=(240, 245, 250),
            text_color=self.palette.text_dark,
            text_secondary=(64, 96, 144),
            accent_color=(32, 96, 192),
            border_radius=6,
        )
