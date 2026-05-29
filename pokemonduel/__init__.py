import logging

from .core.registry import load_all

log = logging.getLogger("dueler.init")

guildowner = 1234


async def setup(bot):
    # 1. Load all static game data into memory before any cog tries to query forms, moves, abilities, etc.
    load_all()
    log.info("Static registries loaded.")

    # 2. Connect to MongoDB and Redis (non-blocking, tolerant of missing Redis).
    try:
        from .core.database import connect as db_connect
        from .core.cache import connect as cache_connect

        await db_connect()
        await cache_connect()

        # 3. Ensure database indexes exist.
        from .services.player_service import PlayerService
        from .services.team_service import TeamService
        await PlayerService().ensure_indexes()
        await TeamService().ensure_indexes()
        log.info("Database layer initialised.")
    except RuntimeError as exc:
        # MONGO_URI not set — bot runs in degraded mode (JSON fallback).
        log.warning("Database not available: %s — running in degraded mode.", exc)
    except Exception as exc:
        log.error("Database initialisation failed: %s", exc, exc_info=True)

    from .cog.commands import PokemonDuel
    from .cog.party_cog import PartyCog
    from .cog.teambuilder_cog import TeambuilderCog
    from .cog.economy_cog import EconomyCog
    from .cog.admin_cog import AdminCog
    from .cog.settings_cog import SettingsCog

    cogs = [
        PokemonDuel(bot),
        PartyCog(bot),
        TeambuilderCog(bot),
        EconomyCog(bot),
        AdminCog(bot),
        SettingsCog(bot),
    ]

    for cog in cogs:
        try:
            await bot.add_cog(cog)
            log.info("Loaded cog: %s", cog.qualified_name)
        except Exception as exc:
            log.error("Failed to load cog %s: %s", type(cog).__name__, exc, exc_info=True)
