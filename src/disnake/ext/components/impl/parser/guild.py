"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, helpers, snowflake

__all__: typing.Sequence[str] = ("GuildParser", "GetGuildParser")


def _get_guild(
    source: typing.Union[helpers.BotAware, helpers.GuildAware],
    argument: str,
) -> disnake.Guild:
    if isinstance(source, helpers.BotAware):
        guild = source.bot.get_guild(int(argument))

        if guild is None and isinstance(source, helpers.GuildAware) and source.guild:
            return source.guild

    elif source.guild:
        return source.guild

    msg = f"Could not find a guild with id {argument!r}."
    raise LookupError(msg)


async def _fetch_guild(
    source: typing.Union[helpers.BotAware, helpers.GuildAware],
    argument: str,
) -> disnake.Guild:
    id_ = int(argument)
    if isinstance(source, helpers.BotAware):
        guild = source.bot.get_guild(id_)
        if guild:
            return guild

        try:
            return await source.bot.fetch_guild(id_)
        except disnake.HTTPException:
            if isinstance(source, helpers.GuildAware) and source.guild:
                return source.guild

    elif source.guild:
        return source.guild

    msg = f"Could not find a guild with id {argument!r}."
    raise LookupError(msg)


GetGuildParser = base.Parser.from_funcs(
    _get_guild, snowflake.snowflake_dumps, is_default_for=(disnake.Guild,)
)
GuildParser = base.Parser.from_funcs(
    _fetch_guild, snowflake.snowflake_dumps, is_default_for=(disnake.Guild,)
)
