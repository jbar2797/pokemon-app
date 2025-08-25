"""Pokémon Pricer package."""

from __future__ import annotations

try:  # pragma: no cover
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("pokemon-pricer")
    except PackageNotFoundError:
        __version__ = "0.1.0"
except Exception:  # pragma: no cover
    __version__ = "0.1.0"

__all__ = ["__version__"]
