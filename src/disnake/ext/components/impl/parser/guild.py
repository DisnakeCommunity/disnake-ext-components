"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GuildParser",
    "GetGuildParser"
)


def _get_guild(inter: disnake.Interaction, argument: str) -> disnake.Guild:
    guild = inter.bot.get_guild(int(argument))

    if guild is None:
        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    return guild

async def _fetch_guild(inter: disnake.Interaction, argument: str) -> disnake.Guild:
    guild = await inter.bot.fetch_guild(int(argument))
    return guild

GetGuildParser = base.Parser.from_funcs(
    _get_guild, snowflake.snowflake_dumps, is_default_for=(disnake.Guild,)
)
GuildParser = base.Parser.from_funcs(
    _fetch_guild, snowflake.snowflake_dumps, is_default_for=(disnake.Guild,)
)
