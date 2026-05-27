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
