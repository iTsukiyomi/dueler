import re

filepath = "pokemonduel/cog/teambuilder_cog.py"

with open(filepath, "r") as f:
    content = f.read()

new_quick_info = """    @commands.command(name="qi", aliases=["quickinfo", "pokemoninfo"])
    async def quick_info(self, ctx: commands.Context, *, poke: str | None = None):
        \"\"\"
        Show details for the selected Pokémon or a specified Pokémon species/form.

        Usage:
          ;qi
          ;qi <pokemon_name>
        \"\"\"
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        theme = profile.get("theme", "light") if profile else "light"
        gen = profile.get("gen", 5) if profile else 5
        
        from ..canvas import BattleRenderer
        from ..canvas.themes import get_palette
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir, palette=get_palette(gen, theme))

        if poke is None:
            ws = await self._load_workspace(ctx)
            if ws is None:
                return
            poke_data = ws["pokemon"]
            slot_text = str(ws['slot_idx'] + 1) if ws.get('slot_idx') is not None else "Workspace"
            team_text = ws.get('team_name', 'Unknown')
            footer_text = f"Team: {team_text} │ Slot: {slot_text}"
        else:
            from ..core.registry import FORMS
            from ..pokemon.pokemon_utils import resolve_form_identifier
            
            matched_identifier = resolve_form_identifier(poke)
            if not matched_identifier:
                await ctx.send(f"Pokémon **{poke}** not found in the forms database.")
                return

            form_info = FORMS.get(matched_identifier)
            if form_info is None:
                await ctx.send(f"Error: form info not found for {matched_identifier}.")
                return
                
            poke_data = {
                "pokname": matched_identifier,
                "hpiv": 31, "atkiv": 31, "defiv": 31, "spatkiv": 31, "spdefiv": 31, "speediv": 31,
                "hpev": 0, "atkev": 0, "defev": 0, "spatkev": 0, "spdefev": 0, "speedev": 0,
                "moves": ["tackle", "tackle", "tackle", "tackle"],
                "ability_index": 0,
                "hitem": "None",
                "nature": "Serious"
            }
            footer_text = "Search Result"

        # Resolve types for the card
        pokname = poke_data.get("pokname", "")
        type_names = renderer._get_type_names(pokname)

        try:
            import asyncio
            loop = asyncio.get_running_loop()
            img_buf = await loop.run_in_executor(
                None,
                renderer.render_pokemon_card,
                poke_data,
                ctx.author.name,
                type_names
            )
            file = discord.File(fp=img_buf, filename="pokemon_card.png")

            type_str = " / ".join(type_names) if type_names else "Unknown"
            embed = discord.Embed(
                title=f"⚡ {poke_data.get('pokname', '?').replace('-', ' ').title()}",
                description=f"**Type:** {type_str}",
                color=0x3B4CCA,
            )
            embed.set_image(url="attachment://pokemon_card.png")
            embed.set_footer(text=footer_text)

            await ctx.send(embed=embed, file=file)
        except Exception as e:
            import logging
            log = logging.getLogger("dueler.cog.teambuilder")
            log.exception("Failed to render pokemon card for ;qi")
            await ctx.send(f"Error rendering card: {e}")"""

# find start and end of quick_info
start_str = "    @commands.command(name=\"qi\", aliases=[\"quickinfo\", \"pokemoninfo\"])"
# next function is setup
end_str = "async def setup(bot: commands.Bot) -> None:"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_quick_info + "\n\n\n" + content[end_idx:]
    with open(filepath, "w") as f:
        f.write(new_content)
    print("Patched teambuilder_cog.py")
else:
    print("Could not find start or end bounds.")
