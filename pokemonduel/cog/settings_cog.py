import discord
from discord.ext import commands
import io
import logging
from pathlib import Path

from ..services.player_service import PlayerService
from ..canvas import BattleRenderer
from ..canvas.themes.palette import get_palette
from ..core import cache

log = logging.getLogger("dueler.cog.settings")

class SettingsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_svc: PlayerService):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player_svc = player_svc

    async def _render_and_edit(self, interaction: discord.Interaction, profile: dict):
        """Re-render the settings image and edit the original message."""
        theme = profile.get("theme", "firered")
        moveset_img = profile.get("moveset_img", True)

        cached_img = await cache.get_settings_image(str(interaction.user.id))
        if cached_img:
            img_buf = io.BytesIO(cached_img)
        else:
            data_dir = Path(__file__).parent.parent / "data"
            renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
            img_buf = renderer.render_settings_menu(theme, moveset_img=moveset_img)
            await cache.set_settings_image(str(interaction.user.id), img_buf.getvalue())

        file = discord.File(fp=img_buf, filename="settings.png")

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Settings",
            color=0x4CAF50
        )
        embed.set_image(url="attachment://settings.png")
        await interaction.message.edit(embed=embed, attachments=[file])

    async def _update_field(self, interaction: discord.Interaction, field: str, value, label: str):
        """Update a single profile field in DB + cache, then re-render."""
        from ..core.database import get_db
        from ..models.player import COLLECTION
        from datetime import datetime, timezone

        await cache.invalidate_settings_image(str(interaction.user.id))
        await cache.invalidate_player_profile(str(interaction.user.id))

        db = get_db()
        await db[COLLECTION].find_one_and_update(
            {"_id": str(interaction.user.id)},
            {"$set": {
                field: value,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        doc = await db[COLLECTION].find_one({"_id": str(interaction.user.id)})
        if doc:
            await cache.set_player_profile(str(interaction.user.id), doc)

        await interaction.response.send_message(
            f"Changed {label} to **{str(value).upper() if isinstance(value, str) else ('IMAGE' if value else 'TEXT')}**.",
            ephemeral=True
        )
        if doc:
            await self._render_and_edit(interaction, doc)

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
        await self._update_field(interaction, "theme", new_theme, "theme")

    @discord.ui.select(
        placeholder="Moveset Display Mode...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Image Mode", value="image", description="Themed moveset image", emoji="🖼️"),
            discord.SelectOption(label="Text Mode", value="text", description="Classic text embed", emoji="📝"),
        ],
        row=1
    )
    async def select_moveset_display(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your settings menu.", ephemeral=True)
            return

        profile = await self.player_svc.get_profile(str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return

        new_val = select.values[0] == "image"
        await self._update_field(interaction, "moveset_img", new_val, "moveset display")


class SettingsCog(commands.Cog, name="Settings"):
    """User preferences and settings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._player_svc = PlayerService()

    @commands.command(name="settings")
    async def show_settings(self, ctx: commands.Context):
        """
        Open the Settings menu.
        Configure your global visual theme and moveset display preferences.
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        profile = await self._player_svc.get_profile(str(ctx.author.id))

        if not profile:
            await ctx.send("Could not load profile.")
            return

        theme = profile.get("theme", "firered")
        moveset_img = profile.get("moveset_img", True)

        cached_img = await cache.get_settings_image(str(ctx.author.id))
        if cached_img:
            img_buf = io.BytesIO(cached_img)
        else:
            data_dir = Path(__file__).parent.parent / "data"
            renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
            img_buf = renderer.render_settings_menu(theme, moveset_img=moveset_img)
            await cache.set_settings_image(str(ctx.author.id), img_buf.getvalue())

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
