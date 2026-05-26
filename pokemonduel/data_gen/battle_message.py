import discord
from pathlib import Path
from ..ui import BattlePromptView
from ..canvas import BattleRenderer


async def generate_main_battle_message(battle):
    """Generates a message representing the current state of the battle with sprite images and dynamic HP bars."""
    data_dir = Path(__file__).parent.parent / "data"
    renderer = BattleRenderer(data_dir)
    img_buf = renderer.render_battle_screen(battle)

    # Build description text
    desc = ""
    if battle.weather._weather_type:
        desc += f"Weather: {battle.weather._weather_type.title()}\n"
    if battle.terrain.item:
        desc += f"Terrain: {battle.terrain.item.title()}\n"
    if battle.trick_room.active():
        desc += "Trick Room: Active\n"
    desc += "\n"

    # Add detailed status for each Pokemon
    desc += f"{battle.trainer1.name}'s {battle.trainer1.current_pokemon.name}\n"
    desc += f" HP: {battle.trainer1.current_pokemon.hp}/{battle.trainer1.current_pokemon.starting_hp}\n"
    if battle.trainer1.current_pokemon.nv.current:
        desc += f" Status: {battle.trainer1.current_pokemon.nv.current}\n"
    if battle.trainer1.current_pokemon.substitute:
        desc += " Behind a substitute!\n"
    desc += "\n"
    desc += f"{battle.trainer2.name}'s {battle.trainer2.current_pokemon.name}\n"
    desc += f" HP: {battle.trainer2.current_pokemon.hp}/{battle.trainer2.current_pokemon.starting_hp}\n"
    if battle.trainer2.current_pokemon.nv.current:
        desc += f" Status: {battle.trainer2.current_pokemon.nv.current}\n"
    if battle.trainer2.current_pokemon.substitute:
        desc += " Behind a substitute!\n"

    # Create embed with the battle image
    e = discord.Embed(
        title=f"Battle between {battle.trainer1.name} and {battle.trainer2.name}",
        description=desc)
    e.set_footer(text="Who Wins!?")
    e.set_image(url="attachment://battle_msg.png")

    try:
        battle_view = BattlePromptView(battle)
        file = discord.File(fp=img_buf, filename="battle_msg.png")
        await battle.channel.send(embed=e, file=file, view=battle_view)
    except RuntimeError:
        pass

    return battle_view


async def generate_text_battle_message(battle):
    """
    Send battle.msg in a boilerplate embed.
    Handles the message being too long.
    """
    page = ""
    pages = []
    base_embed = discord.Embed()  # Fixed color
    raw = battle.msg.strip().split("\n")

    for part in raw:
        if len(page + part) > 2000:
            embed = base_embed.copy()
            embed.description = page.strip()
            pages.append(embed)
            page = ""
        page += part + "\n"

    page = page.strip()
    if page:
        embed = base_embed.copy()
        embed.description = page
        pages.append(embed)

    for page in pages:
        await battle.channel.send(embed=page)

    battle.msg = ""