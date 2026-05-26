"""
pokemonduel.data_gen.query
==========================
Backwards-compatible query interface that delegates to the global
in-memory registries instead of opening JSON files on every call.

The ``ctx`` parameter is kept in the function signatures for API
compatibility with existing callers, but it is no longer used —
all data comes from :mod:`pokemonduel.core.registry`.
"""

from __future__ import annotations

from typing import Any

from ..core.registry import get_registry


async def find(ctx, db: str, filter_dict: dict[str, Any]) -> list[dict]:
    """Fetch all matching rows from the named registry.

    Replaces the old implementation that opened and scanned a JSON
    file on every call.  Now delegates to ``_Registry.find()`` which
    uses indexed lookups when possible and falls back to a linear
    scan only for complex multi-field filters.
    """
    registry = get_registry(db)
    return registry.find(filter_dict)


async def find_one(ctx, db: str, filter_dict: dict[str, Any]) -> dict | None:
    """Fetch the first matching row from the named registry."""
    registry = get_registry(db)
    return registry.find_one(filter_dict)