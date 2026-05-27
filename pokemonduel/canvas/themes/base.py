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

    def render_settings_menu(self, current_theme: str) -> io.BytesIO:
        raise NotImplementedError

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

            # Resolve ability dynamically
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

            # Resolve types if not passed
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

            # Base stats from object
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

            # Resolve types
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
