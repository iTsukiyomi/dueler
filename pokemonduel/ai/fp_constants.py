"""
ai/fp_constants.py — Mapping tables that translate dueler's internal string
and integer representations into the poke_engine format that foul-play uses.

All constants here are module-level and frozen after import; nothing in this
file has side-effects or imports the battle engine.
"""
from __future__ import annotations

# ─── ElementType int IDs → poke_engine type strings ──────────────────────────
# Matches pokemonduel.enums.ElementType values
ELEMENT_TYPE_TO_STR: dict[int, str] = {
    1:  "normal",
    2:  "fighting",
    3:  "flying",
    4:  "poison",
    5:  "ground",
    6:  "rock",
    7:  "bug",
    8:  "ghost",
    9:  "steel",
    10: "fire",
    11: "water",
    12: "grass",
    13: "electric",
    14: "psychic",
    15: "ice",
    16: "dragon",
    17: "dark",
    18: "fairy",
    19: "typeless",
}

# ─── Dueler NonVolatileEffect.current → poke_engine status strings ────────────
# Dueler values: "burn", "sleep", "freeze", "paralysis", "poison", "b-poison", ""
DUELER_STATUS_TO_PE: dict[str | None, str] = {
    "burn":      "Burn",
    "sleep":     "Sleep",
    "freeze":    "Freeze",
    "paralysis": "Paralyze",
    "poison":    "Poison",
    "b-poison":  "Toxic",
    "":          "None",
    None:        "None",
}

# ─── Dueler Weather.get() → poke_engine weather strings ─────────────────────
DUELER_WEATHER_TO_PE: dict[str | None, str] = {
    "sun":       "sun",
    "h-sun":     "harshsun",
    "rain":      "rain",
    "h-rain":    "heavyrain",
    "hail":      "hail",
    "snowscape": "snow",
    "snow":      "snow",
    "sandstorm": "sand",
    "h-wind":    "none",   # Delta Stream has no direct PE analog
    "":          "none",
    None:        "none",
}

# ─── Dueler Terrain.item → poke_engine terrain strings ───────────────────────
DUELER_TERRAIN_TO_PE: dict[str | None, str] = {
    "electric": "electricterrain",
    "grassy":   "grassyterrain",
    "misty":    "mistyterrain",
    "psychic":  "psychicterrain",
    None:       "none",
    "":         "none",
}

# ─── Dueler volatile statuses → poke_engine volatile status strings ───────────
# These are the volatile status names that poke_engine recognises.
POKE_ENGINE_VOLATILE_STATUSES = frozenset({
    "confusion",
    "leechseed",
    "substitute",
    "taunt",
    "lockedmove",
    "yawn",
    "partiallytrapped",
    "slowstart",
    "encore",
    "disable",
    "flinch",
    "roost",
    "typechange",
    "silktrap",
    "banefulbunker",
    "spikyshield",
    "protect",
    "endure",
    "dynamax",
})
