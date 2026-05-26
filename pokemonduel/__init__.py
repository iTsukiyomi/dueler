from .cog.commands import PokemonDuel
from .core.registry import load_all

guildowner = 1234


async def setup(bot):
    # Load all static game data into memory before any cog tries to
    # query forms, moves, abilities, etc.  This replaces the per-call
    # json.load() pattern with O(1) hash-table lookups.
    load_all()

    try:
        await bot.add_cog(PokemonDuel(bot))
    except Exception as e:
        print(f"Error occurred while setting up PokemonDuel: {e}")