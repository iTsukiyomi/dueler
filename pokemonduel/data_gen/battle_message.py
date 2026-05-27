import discord
from pathlib import Path
from ..ui import BattlePromptView
from ..canvas import BattleRenderer


async def generate_main_battle_message(battle):
    """Generates a message representing the current state of the battle with sprite images and dynamic HP bars."""
    data_dir = Path(__file__).parent.parent / "data"
    renderer = BattleRenderer(data_dir)
    img_buf = renderer.render_battle_screen(battle)

    # Build description text (classic game-like format)
    desc = ""
    if battle.weather._weather_type:
        desc += f"☀️ Weather: **{battle.weather._weather_type.title()}**\n"
    if battle.terrain.item:
        desc += f"🌿 Terrain: **{battle.terrain.item.title()}**\n"
    if battle.trick_room.active():
        desc += "🔮 **Trick Room** is active!\n"
    if desc:
        desc += "\n"

    # Pokémon status lines
    t1 = battle.trainer1.current_pokemon
    t2 = battle.trainer2.current_pokemon

    desc += f"**{battle.trainer1.name}**'s {t1.name}\n"
    hp1_pct = int(t1.hp / t1.starting_hp * 100) if t1.starting_hp > 0 else 0
    desc += f"  HP: {t1.hp}/{t1.starting_hp} ({hp1_pct}%)\n"
    if t1.nv.current:
        desc += f"  Status: **{t1.nv.current.upper()}**\n"
    if t1.substitute:
        desc += "  *(Behind a substitute)*\n"
    desc += "\n"

    desc += f"**{battle.trainer2.name}**'s {t2.name}\n"
    hp2_pct = int(t2.hp / t2.starting_hp * 100) if t2.starting_hp > 0 else 0
    desc += f"  HP: {t2.hp}/{t2.starting_hp} ({hp2_pct}%)\n"
    if t2.nv.current:
        desc += f"  Status: **{t2.nv.current.upper()}**\n"
    if t2.substitute:
        desc += "  *(Behind a substitute)*\n"

    # Create embed with the battle image
    e = discord.Embed(
        title=f"⚔️ {battle.trainer1.name} vs {battle.trainer2.name}",
        description=desc,
        color=0x3B4CCA,  # Classic Pokémon blue
    )
    e.set_footer(text="What will you do?")
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
    base_embed = discord.Embed(color=0x3B4CCA)  # Classic Pokémon blue
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