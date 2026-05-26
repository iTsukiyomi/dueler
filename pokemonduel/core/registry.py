"""
pokemonduel.core.registry
=========================
Global, in-memory registries for every static game-data JSON file.

Instead of opening and scanning multi-MB JSON files on each query,
this module loads all static data exactly once at bot startup and
indexes it into dictionaries for O(1) lookups.

Usage
-----
During bot startup (before any cog loads):

    from pokemonduel.core.registry import load_all
    load_all()

Anywhere in the codebase:

    from pokemonduel.core.registry import MOVES, FORMS, ABILITIES
    flamethrower = MOVES.get("flamethrower")
    charizard    = FORMS.get("charizard")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("dueler.registry")

# Absolute path to the directory containing all static JSON data files.
_DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Registry container
# ---------------------------------------------------------------------------

class _Registry:
    """
    A thin wrapper around a dict that provides typed helpers and supports
    the legacy ``find`` / ``find_one`` query interface during the migration
    period.

    Each registry is keyed by a single primary field (typically
    ``"identifier"`` or ``"id"``).  A secondary index can be built when
    a second lookup axis is common (e.g. ``pokemon_id`` for stats).
    """

    __slots__ = ("_name", "_primary", "_by_key", "_raw", "_secondary", "_secondary_key")

    def __init__(self, name: str, primary_key: str = "identifier"):
        self._name = name
        self._primary = primary_key
        self._by_key: dict[str | int, dict] = {}
        self._raw: list[dict] = []
        self._secondary: dict[str | int, list[dict]] = {}
        self._secondary_key: str | None = None

    # -- loading -----------------------------------------------------------

    def load(self, filepath: Path, *, secondary_key: str | None = None) -> None:
        """Read *filepath*, index every record by the primary key.

        Supports two JSON shapes:
        - ``list[dict]`` — the standard format (forms.json, moves.json, …)
        - ``dict[str, dict]`` — keyed format (sets.json) where the outer
          key is treated as the primary key directly.
        """
        with open(filepath, "r", encoding="utf-8") as fh:
            raw_json = json.load(fh)

        self._by_key.clear()
        self._secondary.clear()
        self._secondary_key = secondary_key

        # Normalise dict-of-dicts into list-of-dicts so the rest of the
        # code can be format-agnostic.
        if isinstance(raw_json, dict):
            data: list[dict] = []
            for key, val in raw_json.items():
                if isinstance(val, dict):
                    record = {self._primary: key, **val}
                else:
                    record = {self._primary: key, "value": val}
                data.append(record)
        else:
            data = raw_json

        self._raw = data

        for record in data:
            pk = record.get(self._primary)
            if pk is not None:
                # For string keys, normalise to lowercase so that lookups
                # are consistently case-insensitive (e.g. "Flamethrower" → "flamethrower").
                if isinstance(pk, str):
                    pk = pk.lower()
                self._by_key[pk] = record

            if secondary_key is not None:
                sk = record.get(secondary_key)
                if sk is not None:
                    self._secondary.setdefault(sk, []).append(record)

        log.info(
            "Registry %-20s loaded  %d records  (%d indexed by %r)",
            self._name,
            len(data),
            len(self._by_key),
            self._primary,
        )

    # -- primary lookups ---------------------------------------------------

    def get(self, key: str | int) -> dict | None:
        """O(1) lookup by primary key."""
        if isinstance(key, str):
            key = key.lower()
        return self._by_key.get(key)

    def __getitem__(self, key: str | int) -> dict:
        result = self.get(key)
        if result is None:
            raise KeyError(f"{self._name}: no entry for key {key!r}")
        return result

    def __contains__(self, key: str | int) -> bool:
        if isinstance(key, str):
            key = key.lower()
        return key in self._by_key

    # -- secondary lookups -------------------------------------------------

    def by_secondary(self, key: str | int) -> list[dict]:
        """Retrieve all records matching the secondary index key."""
        return self._secondary.get(key, [])

    # -- backwards-compatible query interface ------------------------------

    def find(self, filter_dict: dict[str, Any]) -> list[dict]:
        """
        Linear-scan fallback that matches the old ``query.find()`` API.

        For simple single-key lookups, prefer ``.get()`` or
        ``.by_secondary()`` instead.
        """
        if not filter_dict:
            return list(self._raw)

        # Fast path: filter is just {primary_key: value}
        if len(filter_dict) == 1:
            only_key = next(iter(filter_dict))
            only_val = filter_dict[only_key]
            if only_key == self._primary and not isinstance(only_val, dict):
                hit = self.get(only_val)
                return [hit] if hit else []
            if only_key == self._secondary_key and not isinstance(only_val, dict):
                return list(self.by_secondary(only_val))

        # General case: full scan with mongo-style filter operators
        results: list[dict] = []
        for item in self._raw:
            if _matches(item, filter_dict):
                results.append(item)
        return results

    def find_one(self, filter_dict: dict[str, Any]) -> dict | None:
        """Return the first match, or ``None``."""
        if not filter_dict:
            return self._raw[0] if self._raw else None

        # Fast path for primary key
        if len(filter_dict) == 1:
            only_key = next(iter(filter_dict))
            only_val = filter_dict[only_key]
            if only_key == self._primary and not isinstance(only_val, dict):
                return self.get(only_val)
            if only_key == self._secondary_key and not isinstance(only_val, dict):
                hits = self.by_secondary(only_val)
                return hits[0] if hits else None

        for item in self._raw:
            if _matches(item, filter_dict):
                return item
        return None

    # -- convenience -------------------------------------------------------

    @property
    def all(self) -> list[dict]:
        """Return the full raw list (read-only reference)."""
        return self._raw

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        return f"<Registry {self._name!r} records={len(self._raw)}>"


# ---------------------------------------------------------------------------
# Mongo-style filter matching (supports $nin, $in, $gt, $lt, etc.)
# ---------------------------------------------------------------------------

def _matches(item: dict, filter_dict: dict[str, Any]) -> bool:
    for key, value in filter_dict.items():
        item_val = item.get(key)
        if isinstance(value, dict):
            for op, operand in value.items():
                if op == "$nin":
                    if item_val in operand:
                        return False
                elif op == "$in":
                    if item_val not in operand:
                        return False
                elif op == "$gt":
                    if item_val is None or item_val <= operand:
                        return False
                elif op == "$lt":
                    if item_val is None or item_val >= operand:
                        return False
                elif op == "$gte":
                    if item_val is None or item_val < operand:
                        return False
                elif op == "$lte":
                    if item_val is None or item_val > operand:
                        return False
                elif op == "$ne":
                    if item_val == operand:
                        return False
        else:
            if item_val != value:
                return False
    return True


# ---------------------------------------------------------------------------
# Global registry singletons
# ---------------------------------------------------------------------------

FORMS:             _Registry = _Registry("forms",             "identifier")
MOVES:             _Registry = _Registry("moves",             "identifier")
ABILITIES:         _Registry = _Registry("abilities",         "identifier")
ITEMS:             _Registry = _Registry("items",             "identifier")
NATURES:           _Registry = _Registry("natures",           "identifier")
POKEMON_STATS:     _Registry = _Registry("pokemon_stats",     "pokemon_id")
POKE_ABILITIES:    _Registry = _Registry("poke_abilities",    "ability_id")
PTYPES:            _Registry = _Registry("ptypes",            "id")
TYPE_EFFECTIVENESS: _Registry = _Registry("type_effectiveness", "damage_type_id")
PFILE:             _Registry = _Registry("pfile",             "id")
STAT_TYPES:        _Registry = _Registry("stat_types",        "id")
SETS:              _Registry = _Registry("sets",              "identifier")

# Mapping from the legacy "db name" strings used in query.find(ctx, "forms", ...)
# to the corresponding registry instance.
_REGISTRY_MAP: dict[str, _Registry] = {
    "forms":              FORMS,
    "moves":              MOVES,
    "abilities":          ABILITIES,
    "items":              ITEMS,
    "natures":            NATURES,
    "pokemon_stats":      POKEMON_STATS,
    "poke_abilities":     POKE_ABILITIES,
    "ptypes":             PTYPES,
    "type_effectiveness": TYPE_EFFECTIVENESS,
    "pfile":              PFILE,
    "stat_types":         STAT_TYPES,
    "sets":               SETS,
}


def get_registry(name: str) -> _Registry:
    """Resolve a legacy db-name string to the matching registry."""
    try:
        return _REGISTRY_MAP[name]
    except KeyError:
        raise ValueError(
            f"No registry registered for {name!r}. "
            f"Known registries: {sorted(_REGISTRY_MAP)}"
        )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

_loaded = False


def load_all(data_dir: Path | str | None = None) -> None:
    """
    Populate every global registry from disk.

    Call this exactly once during bot startup, *before* any cog accesses
    game data.  Subsequent calls are silently ignored unless you pass
    ``force=True`` to :func:`reload_all`.
    """
    global _loaded
    if _loaded:
        return

    base = Path(data_dir) if data_dir else _DATA_DIR
    log.info("Loading static game data from %s", base)

    FORMS.load(base / "forms.json")
    MOVES.load(base / "moves.json")
    ABILITIES.load(base / "abilities.json")
    ITEMS.load(base / "items.json")
    NATURES.load(base / "natures.json")
    POKEMON_STATS.load(base / "pokemon_stats.json", secondary_key="pokemon_id")
    POKE_ABILITIES.load(base / "poke_abilities.json", secondary_key="pokemon_id")
    PTYPES.load(base / "ptypes.json")
    TYPE_EFFECTIVENESS.load(base / "type_effectiveness.json")
    PFILE.load(base / "pfile.json")
    STAT_TYPES.load(base / "stat_types.json")

    # sets.json may not be present in every deployment
    sets_path = base / "sets.json"
    if sets_path.exists():
        SETS.load(sets_path)

    _loaded = True
    log.info("All static registries loaded — %d total files indexed.", len(_REGISTRY_MAP))


def reload_all(data_dir: Path | str | None = None) -> None:
    """Force-reload every registry from disk (useful for hot-reloading)."""
    global _loaded
    _loaded = False
    load_all(data_dir)
