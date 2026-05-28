import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

from .base import BaseThemeRenderer

class FireRedRenderer(BaseThemeRenderer):
    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        width, height = 480, 280
        canvas = self.renderer.asset_loader.get_background("trainer_card_bg", width, height, theme="firered").copy()
        draw = ImageDraw.Draw(canvas)

        # 1. Header Title: "TRAINER CARD"
        title_text = "TRAINER CARD"
        bbox = draw.textbbox((0, 0), title_text, font=self.fonts["title"])
        tx = (width - (bbox[2] - bbox[0])) // 2
        ty = 6 + (30 - (bbox[3] - bbox[1])) // 2
        draw.text((tx, ty), title_text, fill=(255, 203, 5, 255), font=self.fonts["title"]) # Gold

        # 2. Main Details Panel (left column)
        # Use GBA sharp double-line border
        self.renderer._draw_classic_panel(draw, 14, 48, 332, 188, fill=self.palette.panel_bg, border=self.palette.frame_dark)

        # Draw Name
        draw.text((24, 56), "NAME:", fill=self.palette.frame_mid, font=self.fonts["small_bold"])
        draw.text((80, 54), username.upper(), fill=self.palette.text_dark, font=self.fonts["body_bold"])

        # Draw ID No.
        id_no = str(player_id)[-5:] if player_id else "00000"
        draw.text((230, 56), f"IDNo. {id_no}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Separator Line
        draw.line([(20, 76), (326, 76)], fill=self.palette.frame_mid, width=1)

        # Detail lines (flat retro look)
        total = wins + losses
        win_rate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"
        rank_val = f"#{rank}" if rank else "Unranked"

        info_items = [
            ("MONEY", f"¥{wallet:,}"),
            ("ELO RATING", f"{elo}"),
            ("RANK", rank_val),
            ("RECORD", f"{wins}W / {losses}L ({win_rate})"),
            ("ACTIVE TEAM", f"{active_team.upper()}"),
        ]

        dy = 82
        for label, val in info_items:
            draw.text((24, dy), label, fill=self.palette.frame_mid, font=self.fonts["small_bold"])
            val_bbox = draw.textbbox((0, 0), val, font=self.fonts["small_bold"])
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((320 - val_w, dy), val, fill=self.palette.text_dark, font=self.fonts["small_bold"])
            dy += 20

        # 3. Avatar Panel
        self.renderer._draw_classic_panel(draw, 346, 48, 466, 168, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark)
        
        avatar_loaded = False
        if avatar_bytes:
            try:
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((108, 108), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (352, 54), avatar_img)
                avatar_loaded = True
            except Exception:
                pass

        if not avatar_loaded:
            cx, cy = 346 + 60, 48 + 60
            r = 30
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=self.palette.panel_bg, outline=self.palette.frame_dark, width=2)
            draw.line([cx - r, cy, cx + r, cy], fill=self.palette.frame_dark, width=2)
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=self.palette.panel_bg_dark, outline=self.palette.frame_dark, width=2)

        # 4. Active Team Section (6 slots in a 2x4 grid box)
        self.renderer._draw_classic_panel(draw, 14, 198, width - 14, 268, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark)

        slot_w, slot_h = 48, 48
        gap = 10
        sx_start = 54
        sy_row1 = 206

        from ...core.registry import FORMS
        for idx in range(6):
            col = idx % 6
            sx = sx_start + col * (slot_w + gap)
            # Sharp slot border
            self.renderer._draw_classic_panel(draw, sx, sy_row1, sx + slot_w, sy_row1 + slot_h, fill=self.palette.panel_bg, border=self.palette.frame_dark, border_width=1)

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
                sprite = self.renderer._load_sprite(poke_id, (44, 44), name=poke_name)

            if sprite:
                canvas.paste(sprite, (sx + 2, sy_row1 + 2), sprite)
            elif poke_id:
                draw.text((sx + 20, sy_row1 + 16), "?", fill=self.palette.text_light, font=self.fonts["small_bold"])
            else:
                # Tiny Pokéball outline
                cx, cy = sx + 24, sy_row1 + 24
                r = 10
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=self.palette.panel_bg, outline=self.palette.frame_mid, width=1)
                draw.line([cx - r, cy, cx + r, cy], fill=self.palette.frame_mid, width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer", 
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        data = self.parse_pokemon_data(poke, type_names)
        width, height = 500, 310
        canvas = self.renderer.asset_loader.get_background("card_bg", width, height, theme="firered").copy()
        draw = ImageDraw.Draw(canvas)

        # 1. Header block
        self.renderer._draw_header_bar(draw, 4, 8, width - 4, 26, text=data["display_name"].upper(), bg=None)

        if data["type_names"]:
            badge_x = width - 10
            for tn in reversed(data["type_names"]):
                bw = 58
                badge_x -= bw + 4
                self.renderer._draw_type_badge(draw, badge_x, 10, tn, width=bw, height=22)

        # 2. Left side: Sprite box (FireRed GBA double outline, solid fill)
        self.renderer._draw_classic_panel(draw, 14, 44, 164, 194, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark)
        sprite = self.renderer._load_sprite(data["poke_id"], (130, 130), name=data["poke_name"])
        if sprite:
            canvas.paste(sprite, (24, 54), sprite)
        else:
            draw.text((80, 100), "?", fill=self.palette.text_light, font=self.fonts["title"])

        # Labeled item & nature below sprite
        draw.text((20, 204), f"NATURE: {str(data['nature']).upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
        draw.text((20, 222), f"HELD ITEM:", fill=self.palette.text_mid, font=self.fonts["small_bold"])
        draw.text((20, 238), str(data["item"]).replace('-', ' ').upper(), fill=self.palette.text_dark, font=self.fonts["small"])

        # 3. Right side Info Panel (Ability, OT, Stats)
        info_x = 180
        # OT and Ability
        draw.text((info_x, 48), f"OT: {player_name.upper()}", fill=self.palette.text_mid, font=self.fonts["small_bold"])
        draw.text((info_x, 68), f"ABILITY: {str(data['ability']).replace('-', ' ').upper()}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Stats Grid (flat GBA table style)
        stats_y = 96
        draw.text((info_x, stats_y), "STAT   BASE   IV   EV", fill=self.palette.header_bg, font=self.fonts["small_bold"])
        draw.line([(info_x, stats_y + 14), (width - 16, stats_y + 14)], fill=self.palette.frame_dark, width=1)

        stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        stats_labels = ["HP ", "ATK", "DEF", "SPA", "SPD", "SPE"]

        for idx, key in enumerate(stats_keys):
            y_offset = stats_y + 18 + (idx * 15)
            lbl = stats_labels[idx]
            bs_v = data["base_stats"].get(key, 0)
            iv_v = data["ivs"].get(key, 31)
            ev_v = data["evs"].get(key, 0)

            draw.text((info_x, y_offset), f"{lbl:<5}", fill=self.palette.text_dark, font=self.fonts["small_bold"])
            draw.text((info_x + 60, y_offset), f"{bs_v:<5}", fill=self.palette.text_dark, font=self.fonts["small"])
            draw.text((info_x + 120, y_offset), f"{iv_v:<4}", fill=self.palette.text_dark, font=self.fonts["small"])
            draw.text((info_x + 180, y_offset), f"{ev_v:<4}", fill=self.palette.text_dark, font=self.fonts["small"])

        # 4. Moves panel (bottom)
        moves_y = 252
        self.renderer._draw_classic_panel(draw, 14, moves_y, width - 14, height - 10, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark)

        # Draw moves listed horizontally
        draw.text((20, moves_y + 4), "MOVES:", fill=self.palette.frame_mid, font=self.fonts["small_bold"])
        
        move_x_coords = [80, 180, 280, 380]
        for idx, move in enumerate(data["moves"][:4]):
            if idx >= len(move_x_coords):
                break
            mx = move_x_coords[idx]
            if isinstance(move, str):
                m_name = move.replace('-', ' ').upper()
            else:
                m_name = getattr(move, 'pretty_name', str(move)).upper()
            
            draw.text((mx, moves_y + 12), f"• {m_name}", fill=self.palette.text_dark, font=self.fonts["small_bold"])

        # Outer double line
        draw.rectangle([0, 0, width - 1, height - 1], outline=self.palette.frame_dark, width=3)
        draw.rectangle([4, 4, width - 5, height - 5], outline=self.palette.frame_dark, width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def render_moveset(self, pokemon_name: str, moves_data: list[dict],
                       page: int, total_pages: int, total_moves: int) -> io.BytesIO:
        return self._render_moveset_table(
            pokemon_name, moves_data, page, total_pages, total_moves,
            canvas_bg=self.palette.panel_bg,
            header_bg=self.palette.header_bg,
            panel_bg=self.palette.panel_bg,
            panel_border=self.palette.frame_dark,
            row_alt_bg=self.palette.panel_bg_dark,
            text_color=self.palette.text_dark,
            text_secondary=self.palette.text_mid,
            accent_color=self.palette.frame_mid,
            border_radius=0,
            use_type_color_badges=False,
        )

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True) -> io.BytesIO:
        width, height = 480, 280
        canvas = Image.new("RGBA", (width, height), self.palette.frame_mid)
        draw = ImageDraw.Draw(canvas)

        # Main background container with flat GBA double borders
        self.renderer._draw_classic_panel(draw, 4, 4, width - 4, height - 4, fill=self.palette.panel_bg, border=self.palette.frame_dark)

        # Labeled options list
        self.renderer._draw_header_bar(draw, 12, 12, width - 12, 30, text="OPTION MENU", bg=self.palette.header_bg)

        # Entries inside a double border box
        self.renderer._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark)

        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]

        # Option 1: UI THEME
        cursor_y = 66
        draw.text((24, cursor_y), "▶", fill=self.palette.text_dark, font=font)
        draw.text((48, 64), "UI THEME", fill=self.palette.text_dark, font=font)
        self.renderer._draw_classic_panel(draw, 220, 60, 440, 90, fill=self.palette.panel_bg, border=self.palette.frame_dark, border_width=1)
        draw.text((230, 64), current_theme.upper(), fill=self.palette.text_dark, font=font)

        # Option 2: MOVESET DISPLAY
        draw.text((48, 104), "MOVESET DISPLAY", fill=self.palette.text_dark, font=font)
        moveset_val = "IMAGE" if moveset_img else "TEXT"
        self.renderer._draw_classic_panel(draw, 220, 100, 440, 130, fill=self.palette.panel_bg, border=self.palette.frame_dark, border_width=1)
        draw.text((230, 104), moveset_val, fill=self.palette.text_dark, font=font)

        # Helpful hint footer
        help_txt = "Press dropdown below to switch options."
        draw.text((24, 220), help_txt, fill=self.palette.text_mid, font=font_sm)

        # Outer border double line
        draw.rectangle([0, 0, width - 1, height - 1], outline=self.palette.frame_dark, width=3)
        draw.rectangle([4, 4, width - 5, height - 5], outline=self.palette.frame_dark, width=1)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
