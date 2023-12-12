"""Parser implementations for disnake user types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, helpers, snowflake

__all__: typing.Sequence[str] = (
    "GetUserParser",
    "GetMemberParser",
    "UserParser",
    "MemberParser",
)


def _get_user(source: helpers.BotAware, argument: str) -> disnake.User:
    user = source.bot.get_user(int(argument))

    if user is None:
        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    return user


def _get_member(
    source: typing.Union[
        helpers.GuildAware,
        helpers.MessageAware,
        helpers.ChannelAware,
    ],
    argument: str,
) -> disnake.Member:
    if isinstance(source, helpers.GuildAware):
        guild = source.guild
    elif isinstance(source, helpers.MessageAware):
        guild = source.message.guild
    else:
        guild = getattr(source.channel, "guild", None)

    if guild is None:
        msg = (
            "Impossible to fetch a role from an"
            " interaction that doesn't come from a guild."
        )
        raise TypeError(msg)

    member = guild.get_member(int(argument))

    if member is None:
        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    return member


GetUserParser = base.Parser.from_funcs(
    _get_user,
    snowflake.snowflake_dumps,
    is_default_for=(disnake.User, disnake.abc.User),
)
GetMemberParser = base.Parser.from_funcs(
    _get_member, snowflake.snowflake_dumps, is_default_for=(disnake.Member,)
)


async def _fetch_user(source: helpers.BotAware, argument: str) -> disnake.User:
    id_ = int(argument)
    return (
        source.bot.get_user(id_)
        or await source.bot.fetch_user(id_)
    )  # fmt: skip


async def _fetch_member(
    source: typing.Union[
        helpers.GuildAware,
        helpers.MessageAware,
        helpers.ChannelAware,
    ],
    argument: str,
) -> disnake.Member:
    if isinstance(source, helpers.GuildAware):
        guild = source.guild
    elif isinstance(source, helpers.MessageAware):
        guild = source.message.guild
    else:
        guild = getattr(source.channel, "guild", None)

    if guild is None:
        msg = (
            "Impossible to fetch a member from an"
            " interaction that doesn't come from a guild."
        )
        raise TypeError(msg)

    id_ = int(argument)
    return (
        guild.get_member(id_)
        or await guild.fetch_member(id_)
    )  # fmt: skip


UserParser = base.Parser.from_funcs(
    _fetch_user,
    snowflake.snowflake_dumps,
    is_default_for=(disnake.User, disnake.abc.User),
)
MemberParser = base.Parser.from_funcs(
    _fetch_member, snowflake.snowflake_dumps, is_default_for=(disnake.Member,)
)
