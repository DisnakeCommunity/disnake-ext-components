"""Parser implementations for basic disnake snowflake types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base

__all__: typing.Sequence[str] = ("ObjectParser",)


def snowflake_dumps(argument: disnake.abc.Snowflake) -> str:
    """Dump any kind of :class:`disnake.abc.Snowflake` to a string."""
    return str(argument.id)


ObjectParser = base.Parser.from_funcs(
    lambda _, arg: disnake.Object(int(arg)),
    snowflake_dumps,
    is_default_for=(disnake.abc.Snowflake, disnake.Object),
)
