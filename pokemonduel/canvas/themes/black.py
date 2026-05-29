import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class BlackRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (16, 16, 16))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(255, 255, 255), width=2)
        draw.rectangle([4, 4, width - 5, height - 5], outline=(48, 48, 48), width=1)

        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="UNOVA TRAINER CARD", bg=(32, 32, 32))

        self.renderer._draw_classic_panel(draw, 14, 48, 300, 188, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)

        draw.text((24, 56), "NAME:", fill=(180, 180, 180), font=self.fonts["small_bold"])
        draw.text((70, 54), username.upper(), fill=(255, 255, 255), font=self.fonts["body_bold"])

        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((180, 56), f"IDNo. {id_no}", fill=(255, 255, 255), font=self.fonts["small_bold"])

        draw.line([(20, 76), (290, 76)], fill=(255, 255, 255), width=1)

        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("wins/losses", f"{wins}W / {losses}L"),
            ("ACTIVE TEAM", f"{active_team.upper()}"),
        ]

        dy = 84
        for label, val in info_items:
            draw.text((24, dy), label.upper(), fill=(180, 180, 180), font=self.fonts["small_bold"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((288 - val_w, dy), val, fill=(255, 255, 255), font=self.fonts["small_bold"])
            dy += 22

        self.renderer._draw_classic_panel(draw, 314, 48, 466, 188, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((146, 134), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (317, 51), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 390, 118
            r = 30
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(16, 16, 16), outline=(255, 255, 255), width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=(255, 255, 255), width=2)

        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(16, 16, 16), border=(255, 255, 255), border_width=1, radius=2)

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
                draw.text((cx - 4, cy - 8), "?", fill=(100, 100, 100), font=self.fonts["small_bold"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer",
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        canvas = Image.new("RGBA", (width, height), (16, 16, 16))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(255, 255, 255), width=2)

        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)

        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(48, 48, 48))

        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        draw.text((20, 170), f"OT: {player_name.upper()}", fill=(180, 180, 180), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=(255, 255, 255), font=self.fonts["small_bold"])
        draw.text((20, 198), f"ITEM: {str(data['item']).replace('-', ' ').upper()}", fill=(180, 180, 180), font=self.fonts["tiny"])

        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="POKéMON SKILLS", bg=(48, 48, 48))

        draw.text((200, 48), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(180, 180, 180), font=self.fonts["small_bold"])

        stats_y = 86
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP", "ATK", "DEF", "SpA", "SpD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + (idx * 24)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            draw.text((200, y_offset), lbl, fill=(180, 180, 180), font=self.fonts["small_bold"])
            draw.text((236, y_offset), f"{bs_v:<3}", fill=(255, 255, 255), font=self.fonts["small"])

            max_bar_w = 90
            bar_w = int((bs_v / 200) * max_bar_w)
            bar_w = min(max_bar_w, max(5, bar_w))

            draw.rectangle([276, y_offset + 2, 276 + max_bar_w, y_offset + 10], fill=(48, 48, 48), outline=(64, 64, 64))
            draw.rectangle([276, y_offset + 2, 276 + bar_w, y_offset + 10], fill=(255, 255, 255))

            draw.text((380, y_offset), f"IV {iv_v}", fill=(140, 140, 140), font=self.fonts["tiny"])
            draw.text((424, y_offset), f"EV {ev_v}", fill=(180, 180, 180), font=self.fonts["tiny"])

        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(16, 16, 16), border=(255, 255, 255), border_width=1, radius=2)
        move_names = []
        for move in data["moves"][:4]:
            name = move.replace('-', ' ').upper() if isinstance(move, str) else getattr(move, 'pretty_name', str(move)).upper()
            move_names.append(name)
        draw.text((202, moves_y + 4), "MOVES: " + " │ ".join(move_names), fill=(255, 255, 255), font=self.fonts["tiny"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_moveset(self, pokemon_name: str, moves_data: list[dict],
                       page: int, total_pages: int, total_moves: int) -> io.BytesIO:
        return self._render_moveset_table(
            pokemon_name, moves_data, page, total_pages, total_moves,
            canvas_bg=(16, 16, 16),
            header_bg=(48, 48, 48),
            header_text_color=(255, 255, 255),
            panel_bg=(24, 24, 24),
            panel_border=(255, 255, 255),
            row_alt_bg=(32, 32, 32),
            text_color=(255, 255, 255),
            text_secondary=(180, 180, 180),
            accent_color=(255, 255, 255),
            border_radius=0,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True,
                              help_display: str = "image") -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (16, 16, 16))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(255, 255, 255), width=2)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="C-GEAR SETTINGS", bg=(32, 32, 32))

        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=(24, 24, 24), border=(255, 255, 255), border_width=1)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        draw.text((24, 64), "UI THEME", fill=(180, 180, 180), font=font)
        self.renderer._draw_classic_panel(draw, 220, 60, 440, 86, fill=(16, 16, 16), border=(255, 255, 255), border_width=1, radius=2)
        draw.text((230, 64), current_theme.upper(), fill=(255, 255, 255), font=font)

        draw.text((24, 100), "MOVESET DISPLAY", fill=(180, 180, 180), font=font)
        moveset_val = "IMAGE" if moveset_img else "TEXT"
        self.renderer._draw_classic_panel(draw, 220, 96, 440, 122, fill=(16, 16, 16), border=(255, 255, 255), border_width=1, radius=2)
        draw.text((230, 100), moveset_val, fill=(255, 255, 255), font=font)

        draw.text((24, 136), "HELP DISPLAY", fill=(180, 180, 180), font=font)
        self.renderer._draw_classic_panel(draw, 220, 132, 440, 158, fill=(16, 16, 16), border=(255, 255, 255), border_width=1, radius=2)
        draw.text((230, 136), help_display.upper(), fill=(255, 255, 255), font=font)

        help_txt = "Press dropdown menu below to change."
        draw.text((24, 220), help_txt, fill=(140, 140, 140), font=font_sm)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_help_page(self, category: str, commands_list: list[dict],
                         page: int, total_pages: int) -> io.BytesIO:
        return self._render_help_table(
            category, commands_list, page, total_pages,
            canvas_bg=(16, 16, 16),
            header_bg=(48, 48, 48),
            header_text_color=(255, 255, 255),
            panel_bg=(24, 24, 24),
            panel_border=(255, 255, 255),
            row_alt_bg=(32, 32, 32),
            text_color=(255, 255, 255),
            text_secondary=(180, 180, 180),
            accent_color=(255, 255, 255),
            border_radius=0,
        )
