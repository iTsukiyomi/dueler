import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pokemonduel.canvas import BattleRenderer
from pokemonduel.canvas.themes.palette import get_palette

def test_rendering():
    data_dir = Path(__file__).parent / "data"
    
    # Dummy pokemon dict
    poke = {
        "pokname": "pikachu",
        "nickname": "Sparky",
        "nature": "Jolly",
        "ability": "Static",
        "hitem": "Light Ball",
        "hpiv": 31, "atkiv": 31, "defiv": 31, "spatkiv": 31, "spdefiv": 31, "speediv": 31,
        "hpev": 4, "atkev": 252, "defev": 0, "spatkev": 0, "spdefev": 0, "speedev": 252,
        "moves": ["thunderbolt", "quick-attack", "iron-tail", "surf"]
    }
    
    test_out = Path(__file__).parent / "scratch_images"
    test_out.mkdir(exist_ok=True)
    
    themes = ["firered", "heartgold", "platinum", "black", "x", "sun", "sword", "scarlet"]
    
    for theme in themes:
        palette = get_palette(theme)
        renderer = BattleRenderer(data_dir, palette=palette, theme=theme)
        
        # 1. Summary Card
        try:
            card_buf = renderer.render_pokemon_card(poke)
            with open(test_out / f"card_{theme}.png", "wb") as f:
                f.write(card_buf.read())
            print(f"Rendered Summary Card for theme {theme.upper()} successfully.")
        except Exception as e:
            print(f"ERROR Summary Card {theme}: {e}")
            import traceback
            traceback.print_exc()

        # 2. Trainer Card
        try:
            tc_buf = renderer.render_trainer_card(
                username="Gojo",
                player_id="123456789012345678",
                rank=1,
                elo=1500,
                wins=25,
                losses=12,
                wallet=9800,
                active_team="Galar Stars",
                party_pokemon=[poke, poke, poke]
            )
            with open(test_out / f"trainer_{theme}.png", "wb") as f:
                f.write(tc_buf.read())
            print(f"Rendered Trainer Card for theme {theme.upper()} successfully.")
        except Exception as e:
            print(f"ERROR Trainer Card {theme}: {e}")
            import traceback
            traceback.print_exc()

        # 3. Settings Menu
        try:
            settings_buf = renderer.render_settings_menu(theme)
            with open(test_out / f"settings_{theme}.png", "wb") as f:
                f.write(settings_buf.read())
            print(f"Rendered Settings Menu for theme {theme.upper()} successfully.")
        except Exception as e:
            print(f"ERROR Settings Menu {theme}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_rendering()
