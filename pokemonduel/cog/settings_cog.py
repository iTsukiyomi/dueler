import discord
from discord.ext import commands
import logging
from pathlib import Path

from ..services.player_service import PlayerService
from ..canvas import BattleRenderer
from ..canvas.themes.palette import get_palette

log = logging.getLogger("dueler.cog.settings")

class SettingsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_svc: PlayerService):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player_svc = player_svc

    async def _update_settings(self, interaction: discord.Interaction, theme: str):
        # Update db
        from ..core.database import get_db
        from ..models.player import COLLECTION
        from datetime import datetime, timezone
        
        db = get_db()
        await db[COLLECTION].find_one_and_update(
            {"_id": str(interaction.user.id)},
            {"$set": {
                "theme": theme,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        # Update cache in player_service
        doc = await db[COLLECTION].find_one({"_id": str(interaction.user.id)})
        if doc:
            await self.player_svc._repo._cache_profile(str(interaction.user.id), doc)
            
        # Re-render image
        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
        img_buf = renderer.render_settings_menu(theme)
        file = discord.File(fp=img_buf, filename="settings.png")
        
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Settings",
            color=0x4CAF50
        )
        embed.set_image(url="attachment://settings.png")
        
        await interaction.response.send_message(
            f"Changed theme to {theme.upper()}.",
            ephemeral=True
        )
        # We edit the original message to show the new image
        await interaction.message.edit(embed=embed, attachments=[file])

    @discord.ui.select(
        placeholder="Select Game Theme...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="FireRed / LeafGreen", value="firered", description="GBA Era"),
            discord.SelectOption(label="HeartGold / SoulSilver", value="heartgold", description="DS Johto Style"),
            discord.SelectOption(label="Platinum", value="platinum", description="DS Sinnoh Style"),
            discord.SelectOption(label="Black / White", value="black", description="DS High-Contrast"),
            discord.SelectOption(label="X / Y", value="x", description="3DS Kalos Style"),
            discord.SelectOption(label="Sun / Moon", value="sun", description="3DS Alola Passport"),
            discord.SelectOption(label="Sword / Shield", value="sword", description="Switch Galar League Card"),
            discord.SelectOption(label="Scarlet / Violet", value="scarlet", description="Switch SV Rotom App"),
        ],
        row=0
    )
    async def select_theme(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your settings menu.", ephemeral=True)
            return
            
        profile = await self.player_svc.get_profile(str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return
            
        new_theme = select.values[0]
        await self._update_settings(interaction, new_theme)


class SettingsCog(commands.Cog, name="Settings"):
    """User preferences and settings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._player_svc = PlayerService()

    @commands.command(name="settings")
    async def show_settings(self, ctx: commands.Context):
        """
        Open the Settings menu.
        Configure your global visual theme matching a specific Pokémon game.
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        
        if not profile:
            await ctx.send("Could not load profile.")
            return
            
        theme = profile.get("theme", "firered")
        
        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
        
        img_buf = renderer.render_settings_menu(theme)
        file = discord.File(fp=img_buf, filename="settings.png")
        
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Settings",
            color=0x4CAF50
        )
        embed.set_image(url="attachment://settings.png")
        
        view = SettingsView(ctx, self._player_svc)
        await ctx.send(embed=embed, file=file, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SettingsCog(bot))
