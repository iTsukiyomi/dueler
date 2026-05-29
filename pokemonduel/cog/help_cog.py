import asyncio
import io
from pathlib import Path
import discord
from discord.ext import commands

from ..services.player_service import PlayerService
from ..canvas import BattleRenderer
from ..canvas.themes.palette import get_palette
from ..core import cache

HELP_COMMANDS = {
    "battle": [
        {"name": "duel", "usage": "duel <@user>", "desc": "Challenge another player to a live battle."},
        {"name": "inverse", "usage": "inverse <@user>", "desc": "Challenge with type effectiveness inverted."},
        {"name": "random", "usage": "random <@user>", "desc": "Challenge with randomly generated teams."},
        {"name": "npc", "usage": "npc <level>", "desc": "Challenge a gym-leader caliber neural-network NPC."},
        {"name": "randomnpc", "usage": "randomnpc <level>", "desc": "Challenge a neural-network NPC with random teams."},
        {"name": "npcvsnpc", "usage": "npcvsnpc <level1> <level2>", "desc": "Watch two neural-network NPCs battle it out."}
    ],
    "teambuilder": [
        {"name": "select", "usage": "select <pokemon>", "desc": "Choose a Pokémon to edit in your teambuilding slot."},
        {"name": "learn", "usage": "learn <move>", "desc": "Teach a learned move to your currently selected Pokémon."},
        {"name": "ability", "usage": "ability <name>", "desc": "Set the ability of your currently selected Pokémon."},
        {"name": "moveset", "usage": "moveset [pokemon]", "desc": "View all legal moves for a Pokémon."},
        {"name": "iv", "usage": "iv <stat> <value>", "desc": "Set an IV stat (0-31) on your selected Pokémon."},
        {"name": "evs", "usage": "evs <stat1> <val1> ...", "desc": "Allocate EV stats (max 510 total, 252 per stat)."},
        {"name": "nature", "usage": "nature <name>", "desc": "Set the nature of your currently selected Pokémon."},
        {"name": "item", "usage": "item <name>", "desc": "Hold an item on your currently selected Pokémon."},
        {"name": "qi", "usage": "qi <pokemon>", "desc": "View the stats, moves, EVs/IVs card of a Pokémon."}
    ],
    "party": [
        {"name": "party create", "usage": "party create <name>", "desc": "Create a new blank custom party preset."},
        {"name": "party load", "usage": "party load <name>", "desc": "Load a saved party preset into active use."},
        {"name": "party list", "usage": "party list", "desc": "List all your saved party presets."},
        {"name": "party delete", "usage": "party delete <name>", "desc": "Delete a saved party preset from database."},
        {"name": "party add", "usage": "party add <slot> <pokemon>", "desc": "Add a Pokémon to a slot in your active party."},
        {"name": "party view", "usage": "party view [name]", "desc": "Inspect a party preset or your active party."},
        {"name": "party save", "usage": "party save <name>", "desc": "Save your current active party as a preset."}
    ],
    "economy": [
        {"name": "balance", "usage": "balance [@user]", "desc": "Check PokéDollar balance and wallet info."},
        {"name": "leaderboard", "usage": "leaderboard", "desc": "View ELO rankings and top dueling trainers."},
        {"name": "rank", "usage": "rank [@user]", "desc": "View global ladder standing and ELO rating."},
        {"name": "profile", "usage": "profile [@user]", "desc": "Inspect trainer card, wins/losses, active team."},
        {"name": "info", "usage": "info <pokemon>", "desc": "Search base stats, type, and info of a Pokémon."}
    ],
    "settings_admin": [
        {"name": "settings", "usage": "settings", "desc": "Open settings to edit theme & display mode."},
        {"name": "help", "usage": "help [category]", "desc": "View this paginated command help index."},
        {"name": "setprefix", "usage": "setprefix <prefix>", "desc": "Change prefix for bot commands in this guild."},
        {"name": "migrate", "usage": "migrate", "desc": "Run pending database schema migrations (Admin)."},
        {"name": "dbstatus", "usage": "dbstatus", "desc": "View active database connection status (Admin)."},
        {"name": "reloaddata", "usage": "reloaddata", "desc": "Reload internal game data files (Admin)."},
        {"name": "trainnpc", "usage": "trainnpc", "desc": "Train the neural-network NPC weights (Admin)."},
        {"name": "reloadai", "usage": "reloadai", "desc": "Hot-reload the neural-network weights (Admin)."},
        {"name": "aistats", "usage": "aistats", "desc": "Check neural network engine performance stats (Admin)."}
    ]
}

class HelpPaginatorView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_svc: PlayerService, initial_page: int = 0):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player_svc = player_svc
        self.current_page = initial_page
        self.categories = ["battle", "teambuilder", "party", "economy", "settings_admin"]
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Update disable states for previous and next buttons."""
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page == len(self.categories) - 1

    async def _render_and_edit(self, interaction: discord.Interaction) -> None:
        """Re-render the help menu based on pagination change and update the message."""
        self._update_buttons()
        profile = await self.player_svc.get_profile(str(self.ctx.author.id))
        if not profile:
            profile = {}

        help_display = profile.get("help_display", "image")
        theme = profile.get("theme", "firered")
        category = self.categories[self.current_page]
        commands_list = HELP_COMMANDS[category]
        total_pages = len(self.categories)
        page_num = self.current_page + 1

        if help_display == "image":
            cached_img = await cache.get_help_image(str(self.ctx.author.id), category, page_num)
            if cached_img:
                img_buf = io.BytesIO(cached_img)
            else:
                data_dir = Path(__file__).parent.parent / "data"
                renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
                img_buf = await asyncio.to_thread(
                    renderer.render_help_page,
                    category,
                    commands_list,
                    page_num,
                    total_pages
                )
                await cache.set_help_image(str(self.ctx.author.id), category, page_num, img_buf.getvalue())

            file = discord.File(fp=img_buf, filename="help.png")
            embed = discord.Embed(title="Pokémon Duel Help Menu", color=0x2196F3)
            embed.set_image(url="attachment://help.png")
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            embed = discord.Embed(
                title=f"HELP — {category.replace('_', ' & ').upper()}",
                description=f"Page {page_num} of {total_pages}",
                color=0x2196F3
            )
            for cmd in commands_list:
                embed.add_field(name=f";{cmd['usage']}", value=cmd["desc"], inline=False)
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)

    @discord.ui.select(
        placeholder="Select Help Category...",
        options=[
            discord.SelectOption(label="Battle", value="battle", description="Dueling and match commands", emoji="⚔️"),
            discord.SelectOption(label="Teambuilder", value="teambuilder", description="Pokémon customization", emoji="🛠️"),
            discord.SelectOption(label="Party", value="party", description="Party setup and presets", emoji="👥"),
            discord.SelectOption(label="Economy", value="economy", description="Balances, ELO rank, profile info", emoji="💰"),
            discord.SelectOption(label="Settings & Admin", value="settings_admin", description="Preferences & admin tools", emoji="⚙️"),
        ],
        row=0
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu is not yours.", ephemeral=True)
            return
        self.current_page = self.categories.index(select.values[0])
        await self._render_and_edit(interaction)

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.blurple, row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu is not yours.", ephemeral=True)
            return
        self.current_page -= 1
        await self._render_and_edit(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple, row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu is not yours.", ephemeral=True)
            return
        self.current_page += 1
        await self._render_and_edit(interaction)

class HelpCog(commands.Cog, name="Help"):
    """Command helper menu."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._player_svc = PlayerService()

    @commands.command(name="help")
    async def show_help(self, ctx: commands.Context, category_name: str = None) -> None:
        """
        Open the themed Help menu.
        Browse all dueling, economy, party, and settings commands.
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        if not profile:
            profile = {}

        help_display = profile.get("help_display", "image")
        theme = profile.get("theme", "firered")

        categories = ["battle", "teambuilder", "party", "economy", "settings_admin"]
        initial_page = 0
        if category_name:
            norm_cat = category_name.lower().strip()
            if norm_cat in ["settings", "admin", "settings_admin", "settings & admin"]:
                initial_page = 4
            elif norm_cat in categories:
                initial_page = categories.index(norm_cat)

        view = HelpPaginatorView(ctx, self._player_svc, initial_page)
        view._update_buttons()

        category = categories[initial_page]
        commands_list = HELP_COMMANDS[category]
        total_pages = len(categories)
        page_num = initial_page + 1

        if help_display == "image":
            cached_img = await cache.get_help_image(str(ctx.author.id), category, page_num)
            if cached_img:
                img_buf = io.BytesIO(cached_img)
            else:
                data_dir = Path(__file__).parent.parent / "data"
                renderer = BattleRenderer(data_dir, palette=get_palette(theme), theme=theme)
                img_buf = await asyncio.to_thread(
                    renderer.render_help_page,
                    category,
                    commands_list,
                    page_num,
                    total_pages
                )
                await cache.set_help_image(str(ctx.author.id), category, page_num, img_buf.getvalue())

            file = discord.File(fp=img_buf, filename="help.png")
            embed = discord.Embed(title="Pokémon Duel Help Menu", color=0x2196F3)
            embed.set_image(url="attachment://help.png")
            await ctx.send(embed=embed, file=file, view=view)
        else:
            embed = discord.Embed(
                title=f"HELP — {category.replace('_', ' & ').upper()}",
                description=f"Page {page_num} of {total_pages}",
                color=0x2196F3
            )
            for cmd in commands_list:
                embed.add_field(name=f";{cmd['usage']}", value=cmd["desc"], inline=False)
            await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
