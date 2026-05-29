import io
from typing import Optional, List, Dict, Any

class BaseThemeRenderer:
    def __init__(self, renderer):
        self.renderer = renderer
        self.palette = renderer.palette
        self.fonts = renderer.fonts

    def render_trainer_card(self, username: str, player_id: str, rank: Optional[int | str],
                            elo: int, wins: int, losses: int, wallet: int,
                            active_team: str, avatar_bytes: Optional[bytes] = None,
                            party_pokemon: Optional[List[Dict[str, Any]]] = None) -> io.BytesIO:
        raise NotImplementedError

    def render_pokemon_card(self, poke: Any, player_name: str = "Trainer",
                            type_names: Optional[List[str]] = None) -> io.BytesIO:
        raise NotImplementedError

    def render_settings_menu(self, current_theme: str, *, moveset_img: bool = True) -> io.BytesIO:
        raise NotImplementedError

    def render_moveset(self, pokemon_name: str, moves_data: list[dict],
                       page: int, total_pages: int, total_moves: int) -> io.BytesIO:
        raise NotImplementedError


    _TYPE_ID_TO_NAME = {
        1: "Normal", 2: "Fighting", 3: "Flying", 4: "Poison", 5: "Ground",
        6: "Rock", 7: "Bug", 8: "Ghost", 9: "Steel", 10: "Fire",
        11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
        16: "Dragon", 17: "Dark", 18: "Fairy"
    }

    def _render_moveset_table(
        self,
        pokemon_name: str,
        moves_data: list[dict],
        page: int,
        total_pages: int,
        total_moves: int,
        *,
        canvas_bg: tuple,
        header_bg: tuple,
        header_text_color: tuple = (255, 255, 255),
        panel_bg: tuple,
        panel_border: tuple,
        row_alt_bg: Optional[tuple] = None,
        text_color: tuple,
        text_secondary: tuple,
        accent_color: tuple,
        border_radius: int = 0,
        use_type_color_badges: bool = True,
    ) -> io.BytesIO:
        """Shared moveset table renderer called by all theme subclasses.

        Draws a themed paginated table of moves with columns:
        Name | Type | Category | Power | Accuracy
        """
        from PIL import Image, ImageDraw

        width, height = 560, 420
        canvas = Image.new("RGBA", (width, height), canvas_bg)
        draw = ImageDraw.Draw(canvas)

        self.renderer._draw_header_bar(
            draw, 8, 8, width - 8, 28,
            text=f"{pokemon_name.replace('-', ' ').upper()} — LEARNABLE MOVES",
            bg=header_bg,
        )

        col_x = {"name": 20, "type": 190, "cat": 290, "pwr": 400, "acc": 470}
        hdr_y = 46
        self.renderer._draw_classic_panel(
            draw, 8, 40, width - 8, 62,
            fill=header_bg, border=panel_border, border_width=1, radius=border_radius,
        )
        for label, x in [("MOVE", col_x["name"]), ("TYPE", col_x["type"]),
                          ("CLASS", col_x["cat"]), ("PWR", col_x["pwr"]),
                          ("ACC", col_x["acc"])]:
            draw.text((x, hdr_y), label, fill=header_text_color, font=self.fonts["small_bold"])

        row_h = 28
        start_y = 68
        cat_labels = {1: "STATUS", 2: "PHYSICAL", 3: "SPECIAL"}
        cat_short = {1: "STA", 2: "PHY", 3: "SPC"}

        for idx, move in enumerate(moves_data):
            ry = start_y + idx * row_h
            if row_alt_bg and idx % 2 == 1:
                self.renderer._draw_classic_panel(
                    draw, 8, ry, width - 8, ry + row_h,
                    fill=row_alt_bg, border=row_alt_bg, border_width=0, radius=0,
                )
            else:
                self.renderer._draw_classic_panel(
                    draw, 8, ry, width - 8, ry + row_h,
                    fill=panel_bg, border=panel_bg, border_width=0, radius=0,
                )

            name = move.get("identifier", "").replace("-", " ").title()
            if len(name) > 18:
                name = name[:16] + ".."
            draw.text((col_x["name"], ry + 6), name, fill=text_color, font=self.fonts["small_bold"])

            t_id = move.get("type_id", 0)
            type_name = self._TYPE_ID_TO_NAME.get(t_id, "Normal")
            if use_type_color_badges:
                self.renderer._draw_type_badge(
                    draw, col_x["type"], ry + 4, type_name, width=70, height=18,
                )
            else:
                draw.text((col_x["type"], ry + 6), type_name.upper(), fill=text_secondary, font=self.fonts["small"])

            dmg_class = move.get("damage_class_id", 1)
            cat = cat_short.get(dmg_class, "STA")
            cat_full = cat_labels.get(dmg_class, "STATUS")
            if dmg_class == 2:
                cat_color = (200, 80, 40)
            elif dmg_class == 3:
                cat_color = (80, 120, 200)
            else:
                cat_color = text_secondary
            draw.text((col_x["cat"], ry + 6), cat_full, fill=cat_color, font=self.fonts["small"])

            pwr = move.get("power")
            pwr_text = str(pwr) if pwr is not None else "—"
            draw.text((col_x["pwr"], ry + 6), pwr_text, fill=text_color, font=self.fonts["small"])

            acc = move.get("accuracy")
            acc_text = str(acc) if acc is not None else "—"
            draw.text((col_x["acc"], ry + 6), acc_text, fill=text_color, font=self.fonts["small"])

        table_bottom = start_y + len(moves_data) * row_h + 4
        draw.line([(8, table_bottom), (width - 8, table_bottom)], fill=panel_border, width=1)

        footer_y = height - 34
        page_text = f"Page {page} of {total_pages}  •  {total_moves} moves total"
        pbox = draw.textbbox((0, 0), page_text, font=self.fonts["small"])
        px = (width - (pbox[2] - pbox[0])) // 2
        draw.text((px, footer_y), page_text, fill=text_secondary, font=self.fonts["small"])

        if border_radius == 0:
            draw.rectangle([0, 0, width - 1, height - 1], outline=panel_border, width=3)
            draw.rectangle([3, 3, width - 4, height - 4], outline=panel_border, width=1)
        else:
            draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=border_radius, outline=panel_border, width=3)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def parse_pokemon_data(self, poke: Any, type_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Parses a Pokemon dictionary or object into a standard dictionary structure."""
        from ...core.registry import FORMS, POKE_ABILITIES, ABILITIES

        if isinstance(poke, dict):
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
            base_stats = self.renderer._get_base_stats(poke.get("pokname", ""))

            if type_names is None:
                type_names = self.renderer._get_type_names(poke.get("pokname", ""))

            ivs = {
                "hp": poke.get("hpiv", 31), "atk": poke.get("atkiv", 31),
                "def": poke.get("defiv", 31), "spa": poke.get("spatkiv", 31),
                "spd": poke.get("spdefiv", 31), "spe": poke.get("speediv", 31)
            }
            evs = {
                "hp": poke.get("hpev", 0), "atk": poke.get("atkev", 0),
                "def": poke.get("defev", 0), "spa": poke.get("spatkev", 0),
                "spd": poke.get("spdefev", 0), "spe": poke.get("speedev", 0)
            }
            moves = poke.get("moves", [])
        else:
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

            bs = getattr(poke, 'base_stats', {})
            raw_name_obj = getattr(poke, '_name', '').lower()
            if raw_name_obj in bs:
                bs_raw = bs[raw_name_obj]
            elif name_text.lower() in bs:
                bs_raw = bs[name_text.lower()]
            else:
                bs_raw = bs
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
                base_stats = self.renderer._get_base_stats(getattr(poke, '_name', ''))

            if type_names is None:
                type_names = self.renderer._get_type_names(getattr(poke, '_name', ''))

            ivs = {
                "hp": getattr(poke, "hpiv", 31), "atk": getattr(poke, "atkiv", 31),
                "def": getattr(poke, "defiv", 31), "spa": getattr(poke, "spatkiv", 31),
                "spd": getattr(poke, "spdefiv", 31), "spe": getattr(poke, "speediv", 31)
            }
            evs = {
                "hp": getattr(poke, "hpev", 0), "atk": getattr(poke, "atkev", 0),
                "def": getattr(poke, "defev", 0), "spa": getattr(poke, "spatkev", 0),
                "spd": getattr(poke, "spdefev", 0), "spe": getattr(poke, "speedev", 0)
            }
            moves = getattr(poke, 'moves', [])

        return {
            "poke_id": poke_id,
            "poke_name": poke.get("pokname", "") if isinstance(poke, dict) else getattr(poke, "_name", ""),
            "display_name": display_name,
            "nature": nature_val,
            "ability": ability_val,
            "item": item_val,
            "base_stats": base_stats,
            "type_names": type_names,
            "ivs": ivs,
            "evs": evs,
            "moves": moves
        }
