import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class PlatinumRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (220, 226, 230))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(100, 115, 130), width=3)
        draw.rectangle([3, 3, width - 4, height - 4], outline=(255, 255, 255), width=1)

        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="SINNOH TRAINER CARD", bg=(112, 128, 144))

        self.renderer._draw_classic_panel(draw, 14, 48, 280, 188, fill=(240, 244, 248), border=(112, 128, 144))

        draw.text((24, 56), "NAME:", fill=(96, 112, 128), font=self.fonts["small_bold"])
        draw.text((70, 54), username, fill=self.palette.text_dark, font=self.fonts["body_bold"])

        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((170, 56), f"IDNo. {id_no}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        draw.line([(20, 76), (270, 76)], fill=(180, 192, 208), width=1)

        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("wins/losses", f"{wins}W / {losses}L"),
            ("TEAM", f"{active_team}"),
        ]

        dy = 84
        for label, val in info_items:
            draw.text((24, dy), label.upper(), fill=(96, 112, 128), font=self.fonts["small_bold"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((268 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 22

        self.renderer._draw_classic_panel(draw, 294, 48, 466, 188, fill=(230, 235, 240), border=(112, 128, 144))
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((166, 134), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (297, 51), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 380, 118
            r = 30
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=(112, 128, 144), width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=(112, 128, 144), width=2)

        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=(40, 48, 64), border=(100, 115, 130))

        slot_w, slot_h = 56, 56
        gap = 12
        sx_start = 42
        sy = 203

        from ...core.registry import FORMS
        for idx in range(6):
            sx = sx_start + idx * (slot_w + gap)
            self.renderer._draw_classic_panel(draw, sx, sy, sx + slot_w, sy + slot_h, fill=(60, 72, 96), border=(112, 128, 144), border_width=1, radius=2)

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
                draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(80, 96, 128), outline=(140, 160, 190), width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer",
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        canvas = Image.new("RGBA", (width, height), (220, 226, 230))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(112, 128, 144), width=3)

        self.renderer._draw_classic_panel(draw, 10, 10, 180, 300, fill=(240, 244, 248), border=(112, 128, 144))

        self.renderer._draw_header_bar(draw, 16, 16, 174, 24, text=data["display_name"].upper(), bg=(112, 128, 144))

        sprite = self.renderer._load_sprite(data["poke_id"], (110, 110), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (40, 50), sprite)

        draw.text((20, 170), f"OT: {player_name.upper()}", fill=(112, 128, 144), font=self.fonts["tiny"])
        draw.text((20, 184), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((20, 198), f"ITEM: {str(data['item']).replace('-', ' ').upper()}", fill=(112, 128, 144), font=self.fonts["tiny"])

        if data["type_names"]:
            tx_y = 210
            for tn in data["type_names"]:
                self.renderer._draw_type_badge(draw, 20, tx_y, tn, width=64, height=18)
                tx_y += 22

        self.renderer._draw_classic_panel(draw, 190, 10, 490, 300, fill=(255, 255, 255), border=(112, 128, 144))
        self.renderer._draw_header_bar(draw, 196, 16, 484, 22, text="POKéMON STATS", bg=(96, 112, 128))

        draw.text((200, 48), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=(112, 128, 144), font=self.fonts["small_bold"])

        stats_y = 76
        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP", "ATTACK", "DEFENSE", "SP. ATK", "SP. DEF", "SPEED"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + (idx * 26)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            draw.text((200, y_offset), lbl, fill=(96, 112, 128), font=self.fonts["small_bold"])
            draw.text((290, y_offset), f"{bs_v:<3}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

            if idx < 5:
                draw.line([(200, y_offset + 20), (480, y_offset + 20)], fill=(220, 226, 230), width=1)

            draw.text((360, y_offset), f"IV {iv_v}", fill=(140, 150, 160), font=self.fonts["tiny"])
            draw.text((410, y_offset), f"EV {ev_v}", fill=(100, 120, 140), font=self.fonts["tiny"])

        moves_y = 238
        self.renderer._draw_classic_panel(draw, 196, moves_y, 484, 292, fill=(240, 244, 248), border=(112, 128, 144), border_width=1, radius=2)
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
            canvas_bg=(220, 226, 230),
            header_bg=(112, 128, 144),
            panel_bg=(240, 244, 248),
            panel_border=(112, 128, 144),
            row_alt_bg=(230, 235, 240),
            text_color=self.palette.text_dark,
            text_secondary=(96, 112, 128),
            accent_color=(112, 128, 144),
            border_radius=4,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), (220, 226, 230))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([0, 0, width - 1, height - 1], outline=(112, 128, 144), width=4)
        self.renderer._draw_header_bar(draw, 10, 10, width - 10, 30, text="POKéTCH OPTIONS", bg=(70, 80, 90))

        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 42, fill=(240, 244, 248), border=(112, 128, 144))

        font = self.fonts["body_bold"]

        draw.text((24, 64), "ACTIVE THEME", fill=(96, 112, 128), font=font)
        self.renderer._draw_classic_panel(draw, 220, 60, 440, 90, fill=(255, 255, 255), border=(112, 128, 144), border_width=1, radius=2)
        draw.text((230, 64), current_theme.upper(), fill=self.palette.text_dark, font=font)

        draw.text((24, 104), "MOVESET DISPLAY", fill=(96, 112, 128), font=font)
        moveset_val = "IMAGE" if moveset_img else "TEXT"
        self.renderer._draw_classic_panel(draw, 220, 100, 440, 130, fill=(255, 255, 255), border=(112, 128, 144), border_width=1, radius=2)
        draw.text((230, 104), moveset_val, fill=self.palette.text_dark, font=font)

        self.renderer._draw_classic_panel(draw, 12, height - 36, width - 12, height - 10, fill=(40, 50, 40), border=(112, 128, 144))
        draw.text((24, height - 28), "POKéTCH: Select options via dropdown below.", fill=(100, 255, 100), font=self.fonts["tiny"])

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
