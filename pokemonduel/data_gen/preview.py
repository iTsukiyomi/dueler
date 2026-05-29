import discord
from pathlib import Path
from ..canvas import BattleRenderer


async def generate_team_preview(battle):
    """Generates a message for trainers to preview their team with images."""
    from ..ui.team_preview import PreviewPromptView

    preview_view = PreviewPromptView(battle)

    data_dir = Path(__file__).parent.parent / "data"
    renderer = BattleRenderer(data_dir)
    img_buf = renderer.render_team_preview(battle)

    embed = discord.Embed(
        title=f"⚡ Team Preview",
        description=f"**{battle.trainer1.name}** vs **{battle.trainer2.name}**\nChoose your lead Pokémon!",
        color=0x3B4CCA,
    )

    file = discord.File(fp=img_buf, filename="team_preview.png")
    embed.set_image(url="attachment://team_preview.png")

    await battle.channel.send(embed=embed, file=file, view=preview_view)

    return preview_view
