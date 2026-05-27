import discord
from discord.ext import commands
import logging
import io

from ..services.player_service import PlayerService
from ..canvas import BattleRenderer
from ..canvas.themes import get_palette
from pathlib import Path

log = logging.getLogger("dueler.cog.settings")

class SettingsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_svc: PlayerService):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player_svc = player_svc

    async def _update_settings(self, interaction: discord.Interaction, theme: str, gen: int):
        # Update db
        from ..core.database import get_db
        from ..models.player import COLLECTION
        from datetime import datetime, timezone
        
        db = get_db()
        await db[COLLECTION].find_one_and_update(
            {"_id": str(interaction.user.id)},
            {"$set": {
                "theme": theme,
                "gen": gen,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        # Update cache in player_service
        doc = await db[COLLECTION].find_one({"_id": str(interaction.user.id)})
        if doc:
            await self.player_svc._repo._cache_profile(str(interaction.user.id), doc)
            
        # Re-render image
        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir, palette=get_palette(gen, theme), gen=gen, theme=theme)
        img_buf = renderer.render_settings_menu(theme, gen)
        file = discord.File(fp=img_buf, filename="settings.png")
        
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Settings",
            color=0x4CAF50
        )
        embed.set_image(url="attachment://settings.png")
        
        await interaction.response.send_message(
            f"Changed theme to {theme}. Changed gen to {gen}.",
            ephemeral=True
        )
        # We edit the original message to show the new image
        await interaction.message.edit(embed=embed, attachments=[file])

    @discord.ui.button(label="Toggle Theme (Light/Dark)", style=discord.ButtonStyle.primary, row=0)
    async def toggle_theme(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your settings menu.", ephemeral=True)
            return
            
        profile = await self.player_svc.get_profile(str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return
            
        current_theme = profile.get("theme", "light")
        new_theme = "dark" if current_theme == "light" else "light"
        current_gen = profile.get("gen", 5)
        
        await self._update_settings(interaction, new_theme, current_gen)

    @discord.ui.select(
        placeholder="Select Generation...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Gen 1", value="1", description="GameBoy Monochrome"),
            discord.SelectOption(label="Gen 2", value="2", description="GameBoy Color"),
            discord.SelectOption(label="Gen 3", value="3", description="GameBoy Advance"),
            discord.SelectOption(label="Gen 4", value="4", description="Nintendo DS (DPPt)"),
            discord.SelectOption(label="Gen 5", value="5", description="Nintendo DS (BW)"),
            discord.SelectOption(label="Gen 6-9", value="9", description="Modern 3D Era"),
        ],
        row=1
    )
    async def select_gen(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your settings menu.", ephemeral=True)
            return
            
        profile = await self.player_svc.get_profile(str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return
            
        current_theme = profile.get("theme", "light")
        new_gen = int(select.values[0])
        
        await self._update_settings(interaction, current_theme, new_gen)


class SettingsCog(commands.Cog, name="Settings"):
    """User preferences and settings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._player_svc = PlayerService()

    @commands.command(name="settings")
    async def show_settings(self, ctx: commands.Context):
        """
        Open the Settings menu.
        Configure your global visual theme (Light/Dark) and Generation style (Gen 1-9).
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        
        if not profile:
            await ctx.send("Could not load profile.")
            return
            
        theme = profile.get("theme", "light")
        gen = profile.get("gen", 5)
        
        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir, palette=get_palette(gen, theme), gen=gen, theme=theme)
        
        img_buf = renderer.render_settings_menu(theme, gen)
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
