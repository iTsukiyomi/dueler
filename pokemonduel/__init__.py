from .cog.commands import PokemonDuel

guildowner=1234

async def setup(bot):
    try:
        await bot.add_cog(PokemonDuel(bot))
    except Exception as e:
        print(f"Error occurred while setting up PokemonDuel: {e}")