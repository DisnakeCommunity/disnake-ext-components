from __future__ import annotations

import inspect
import typing as t

import disnake
from disnake.ext import commands

from . import types_

__all__ = ["ALLOW_CONVERTER_FETCHING", "CONVERTER_MAP"]


CollectionT = t.TypeVar("CollectionT", bound=t.Collection[t.Any])
ConverterSig = t.Union[
    t.Callable[..., types_.Coro[t.Any]],
    t.Callable[..., t.Any],
]
ChannelT = t.TypeVar("ChannelT", disnake.abc.GuildChannel, disnake.Thread)
FlagT = t.TypeVar("FlagT", bound=disnake.flags.BaseFlags)


class ALLOW_CONVERTER_FETCHING:  # There's probably a better way of doing this...
    """A configuration namespace used to define whether or not specific converters are allowed to
    fetch if getting from cache fails.
    """

    CHANNELS = False
    """Whether or not to allow converters to fetch a channel if getting it from cache fails."""

    GUILDS = False
    """Whether or not to allow converters to fetch a guild if getting it from cache fails."""

    USERS = False
    """Whether or not to allow converters to fetch a user/member if getting it from cache fails."""

    MESSAGES = False
    """Whether or not to allow converters to fetch a message if getting it from cache fails."""


def collection_converter(
    collection_type: t.Type[CollectionT],
    inner_converter: ConverterSig,
) -> t.Callable[[t.Collection[str], disnake.Interaction, t.List[t.Any]], types_.Coro[CollectionT]]:
    """Create a converter for a given collection type."""

    async def _convert_collection(
        argument: t.Collection[str],
        inter: disnake.Interaction,
        converted: t.List[t.Any],
    ) -> CollectionT:
        newly_converted: t.List[t.Any] = []
        for arg in argument:
            value = inner_converter(arg, inter=inter, converted=converted + newly_converted)
            if inspect.isawaitable(value):
                value = await value

            newly_converted.append(value)

        return collection_type(newly_converted)  # pyright: ignore

    return _convert_collection


def make_channel_converter(type_: t.Type[ChannelT]) -> t.Callable[..., types_.Coro[ChannelT]]:
    """Create a channel converter for a given channel type."""

    async def _convert_channel(argument: str, inter: disnake.Interaction) -> ChannelT:
        id = int(argument)
        if not (channel := inter.bot.get_channel(id)) and ALLOW_CONVERTER_FETCHING.CHANNELS:
            channel = await inter.bot.fetch_channel(id)

        if not channel or not isinstance(channel, type_):
            raise ValueError(f"Could not find a channel of type {type_!r} with id {argument}.")

        return channel

    return _convert_channel


async def user_converter(argument: str, inter: disnake.Interaction) -> disnake.User:
    """Convert a user id to a :class:`disnake.User` in the context of the provided
    :class:`disnake.Interaction`.

    Parameters
    ----------
    inter: :class:`disnake.Interaction`
        The interaction with which to convert the user id.
    argument: :class:`str`
        The user id to be converted.

    Raises
    ------
    commands.UserNotFound:
        The argument could not be converted into a :class:`disnake.User`.

    Returns
    -------
    :class:`disnake.User`
        The user with the provided user id.
    """
    id = int(argument)
    if not (user := inter.bot.get_user(id)) and ALLOW_CONVERTER_FETCHING.USERS:
        user = await inter.bot.fetch_user(id)

    if not user:
        raise ValueError(f"Could not find a user with id {argument}.")

    return user


async def guild_converter(argument: str, inter: disnake.Interaction) -> disnake.Guild:
    """Convert a guild id to a :class:`disnake.Guild` in the context of the provided
    :class:`disnake.Interaction`.

    Parameters
    ----------
    inter: :class:`disnake.Interaction`
        The interaction with which to convert the guild id.
    argument: :class:`str`
        The guild id to be converted.

    Raises
    ------
    commands.GuildNotFound:
        The argument could not be converted into a :class:`disnake.Guild`.

    Returns
    -------
    :class:`disnake.Guild`
        The guild with the provided guild id.
    """
    id = int(argument)
    if not (guild := inter.bot.get_guild(id)) and ALLOW_CONVERTER_FETCHING.GUILDS:
        guild = await inter.bot.fetch_guild(id)

    if not guild:
        raise ValueError(f"Could not find a guild with id {argument}.")

    return guild


async def message_converter(
    argument: str,
    inter: disnake.Interaction,
    converted: t.Optional[t.List[t.Any]] = None,
) -> disnake.Message:
    """Convert a message id to a :class:`disnake.Message` in the context of the provided
    :class:`disnake.Interaction`.

    This converter supports lookback: if any channels have been previously converted for the same
    custom_id, it will also take those channels into consideration when searching the message.

    Parameters
    ----------
    inter: :class:`disnake.Interaction`
        The interaction with which to convert the message id.
    argument: :class:`str`
        The message id to be converted.

    Raises
    ------
    commands.MessageNotFound:
        The argument could not be converted into a :class:`disnake.Message`.

    Returns
    -------
    :class:`disnake.Message`
        The message with the provided message id.
    """
    id = int(argument)

    if message := inter._state._get_message(id):
        return message

    if not ALLOW_CONVERTER_FETCHING.MESSAGES:
        raise commands.MessageNotFound(argument)

    async def _underlying(channel: disnake.abc.Messageable) -> t.Optional[disnake.Message]:
        return await channel.fetch_message(id)

    entries = {inter.channel}.union(converted or {})
    for entry in entries:
        if not isinstance(entry, disnake.abc.Messageable):
            continue
        if message := await _underlying(entry):
            return message

    else:
        raise ValueError(f"Could not find a message with id {argument}.")


async def member_converter(
    argument: str,
    inter: disnake.Interaction,
    converted: t.Optional[t.List[t.Any]] = None,
) -> disnake.Member:
    """Convert a member id to a :class:`disnake.Member` in the context of the provided
    :class:`disnake.Interaction`. This converter only works in the context of a guild.

    This converter supports lookback: if any guilds have been previously converted for the same
    custom_id, it will also take those guilds into consideration when searching the member.

    Parameters
    ----------
    inter: :class:`disnake.Interaction`
        The interaction with which to convert the member id.
    argument: :class:`str`
        The member id to be converted.

    Raises
    ------
    commands.MemberNotFound:
        The argument could not be converted into a :class:`disnake.Member`.

    Returns
    -------
    :class:`disnake.Member`
        The member with the provided member id.
    """
    id = int(argument)

    async def _underlying(guild: disnake.Guild) -> t.Optional[disnake.Member]:
        if not (member := guild.get_member(id)) and ALLOW_CONVERTER_FETCHING.USERS:
            member = await guild.fetch_member(id)
        return member

    entries = {inter.guild}.union(converted or {})
    for entry in entries:
        if not isinstance(entry, disnake.Guild):
            continue
        if member := await _underlying(entry):
            return member

    else:
        raise ValueError(f"Could not find a member with id {argument}.")


async def role_converter(
    argument: str,
    inter: disnake.Interaction,
    converted: t.Optional[t.List[t.Any]] = None,
) -> disnake.Role:
    """Convert a role id to a :class:`disnake.Role` in the context of the provided
    :class:`disnake.Interaction`. This converter only works in the context of a guild.

    This converter supports lookback: if any guilds have been previously converted for the same
    custom_id, it will also take those guilds into consideration when searching the role.

    Parameters
    ----------
    inter: :class:`disnake.Interaction`
        The interaction with which to convert the role id.
    argument: :class:`str`
        The role id to be converted.

    Raises
    ------
    commands.RoleNotFound:
        The argument could not be converted into a :class:`disnake.Role`.

    Returns
    -------
    :class:`disnake.Role`
        The role with the provided role id.
    """
    id = int(argument)

    async def _underlying(guild: disnake.Guild) -> t.Optional[disnake.Role]:
        if not (role := guild.get_role(id)) and ALLOW_CONVERTER_FETCHING.GUILDS:
            all_roles = await guild.fetch_roles()
            role = next((role for role in all_roles if role.id == id), None)
        return role

    entries = {inter.guild}.union(converted or {})
    for entry in entries:
        if not isinstance(entry, disnake.Guild):
            continue
        if role := await _underlying(entry):
            return role

    else:
        raise ValueError(f"Could not find a role with id {argument}.")


def snowflake_to_str(snowflake: disnake.abc.Snowflake) -> str:
    return str(snowflake.id)


def make_flag_converter(type_: t.Type[FlagT]) -> t.Callable[..., FlagT]:
    """Create a flag converter for a given flag type."""

    def _convert_flag(argument: str, inter: disnake.Interaction) -> FlagT:
        return type_._from_value(int(argument))  # pyright: ignore[reportUnknownMemberType]

    return _convert_flag


def flag_to_str(flag: disnake.flags.BaseFlags) -> str:
    return str(flag.value)


# flake8: noqa: E241
CONVERTER_MAP: t.Mapping[type, t.Tuple[ConverterSig, ConverterSig]] = {
    # fmt: off
    str:                      (str,                                              str),
    int:                      (int,                                              str),
    float:                    (float,                                            str),
    bool:                     (commands.converter._convert_to_bool,              str),
    disnake.User:             (user_converter,                                   snowflake_to_str),
    disnake.Member:           (member_converter,                                 snowflake_to_str),
    disnake.Role:             (role_converter,                                   snowflake_to_str),
    disnake.Thread:           (make_channel_converter(disnake.Thread),           snowflake_to_str),
    disnake.TextChannel:      (make_channel_converter(disnake.TextChannel),      snowflake_to_str),
    disnake.VoiceChannel:     (make_channel_converter(disnake.VoiceChannel),     snowflake_to_str),
    disnake.CategoryChannel:  (make_channel_converter(disnake.CategoryChannel),  snowflake_to_str),
    disnake.abc.GuildChannel: (make_channel_converter(disnake.abc.GuildChannel), snowflake_to_str),
    disnake.Guild:            (guild_converter,                                  snowflake_to_str),
    disnake.Message:          (message_converter,                                snowflake_to_str),
    disnake.Permissions:      (make_flag_converter(disnake.Permissions),         flag_to_str),
    # disnake.Emoji:            dpy_converter.EmojiConverter().convert,  # temporarily(?) disabled.
    # fmt: on
}
"""A mapping of a type to a tuple of two converter functions. The first is used to convert from str
to that type, the second is used to convert the type back to str.
"""
