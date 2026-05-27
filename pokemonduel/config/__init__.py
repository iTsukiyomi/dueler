from .config_manager import (
    MemberConfig,
    GuildConfig,
    ConfigManager,
    PartyAttribute,
    UseThreadsAttribute,
    EnhancedMemberConfig,
    EnhancedGuildConfig,
    EnhancedConfigManager,
)


class _PokemonDuelCogStub:
    """Stub whose ``__class__.__name__`` is ``PokemonDuel`` so that
    ``EnhancedConfigManager.get_conf()`` resolves the right data dir."""
    pass

# Rename the class so __class__.__name__ == "PokemonDuel"
_PokemonDuelCogStub.__name__ = "PokemonDuel"
_PokemonDuelCogStub.__qualname__ = "PokemonDuel"

_LEGACY_IDENTIFIER = 145519400223506432


def get_legacy_config() -> EnhancedConfigManager:
    """Return a :class:`EnhancedConfigManager` matching the legacy PokemonDuel cog."""
    return EnhancedConfigManager.get_conf(
        _PokemonDuelCogStub(), identifier=_LEGACY_IDENTIFIER
    )