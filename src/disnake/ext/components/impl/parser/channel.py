"""Parser implementations for disnake channel types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, helpers, snowflake

if typing.TYPE_CHECKING:
    from disnake.ext import commands

    _AnyBot = typing.Union[
        commands.Bot,
        commands.InteractionBot,
        commands.AutoShardedBot,
        commands.AutoShardedInteractionBot,
    ]


__all__: typing.Sequence[str] = (
    "DMChannelParser",
    "ForumChannelParser",
    "GroupChannelParser",
    "GuildChannelParser",
    "PrivateChannelParser",
    "NewsChannelParser",
    "StageChannelParser",
    "TextChannelParser",
    "VoiceChannelParser",
    "CategoryParser",
    "GetDMChannelParser",
    "GetForumChannelParser",
    "GetGroupChannelParser",
    "GetGuildChannelParser",
    "GetPrivateChannelParser",
    "GetNewsChannelParser",
    "GetStageChannelParser",
    "GetTextChannelParser",
    "GetVoiceChannelParser",
    "GetCategoryParser",
    "PartialMessageableParser",
)


_AnyChannel = typing.Union[
    disnake.abc.GuildChannel, disnake.abc.PrivateChannel, disnake.Thread
]
_ChannelT = typing.TypeVar("_ChannelT", bound=_AnyChannel)


def _get_source(
    source: typing.Union[helpers.GuildAware, helpers.BotAware, helpers.MessageAware],
) -> typing.Union[disnake.Guild, _AnyBot]:
    if isinstance(source, helpers.BotAware):
        return source.bot

    elif isinstance(source, helpers.MessageAware):
        actual_source = source.message.guild
        if actual_source:
            return actual_source

    elif source.guild:
        return source.guild

    # TODO: In the future handle just returning message.channel if it
    #       is a DM channel and the id matches the argument.
    msg = "Parsing DM channels from a message is currently not supported."
    raise NotImplementedError(msg)


# GET_ONLY


def _build_sync_channel_parser(
    *types: typing.Type[_ChannelT],
    is_default_for: typing.Optional[typing.Sequence[typing.Type[typing.Any]]] = None,
) -> typing.Type[base.Parser[_ChannelT]]:
    def _get_channel(
        source: typing.Union[
            helpers.GuildAware,
            helpers.BotAware,
            helpers.MessageAware,
        ],
        argument: str,
    ) -> _ChannelT:
        channel = _get_source(source).get_channel(int(argument))
        if channel is None:
            msg = f"Could not find a channel with id {argument!r}."
            raise LookupError(msg)

        if types and not isinstance(channel, types):
            type_str = ", ".join(repr(type_.__name__) for type_ in types)
            msg = (
                f"Found a channel of type {type(channel).__name__!r} for id"
                f"{argument!r}, expected (any of) type(s) {type_str}."
            )
            raise TypeError(msg)

        return typing.cast(_ChannelT, channel)

    return base.Parser.from_funcs(
        _get_channel, snowflake.snowflake_dumps, is_default_for=is_default_for or types
    )


# ABSTRACT

GetGuildChannelParser = _build_sync_channel_parser(disnake.abc.GuildChannel)
GetPrivateChannelParser = _build_sync_channel_parser(disnake.abc.PrivateChannel)


# PRIVATE

GetDMChannelParser = _build_sync_channel_parser(disnake.DMChannel)
GetGroupChannelParser = _build_sync_channel_parser(disnake.GroupChannel)


# GUILD

GetForumChannelParser = _build_sync_channel_parser(disnake.ForumChannel)
GetNewsChannelParser = _build_sync_channel_parser(disnake.NewsChannel)
GetVoiceChannelParser = _build_sync_channel_parser(disnake.VoiceChannel)
GetStageChannelParser = _build_sync_channel_parser(disnake.StageChannel)
GetTextChannelParser = _build_sync_channel_parser(disnake.TextChannel)
GetThreadParser = _build_sync_channel_parser(disnake.Thread)
GetCategoryParser = _build_sync_channel_parser(disnake.CategoryChannel)


# GET AND FETCH


def _build_async_channel_parser(
    *types: typing.Type[_ChannelT],
    is_default_for: typing.Optional[typing.Sequence[typing.Type[typing.Any]]] = None,
) -> typing.Type[base.Parser[_ChannelT]]:
    async def _fetch_channel(inter: disnake.Interaction, argument: str) -> _ChannelT:
        channel_id = int(argument)
        channel = (
            inter.bot.get_channel(channel_id)
            or await inter.bot.fetch_channel(channel_id)
        )  # fmt: skip

        if types and not isinstance(channel, types):
            type_str = ", ".join(repr(type_.__name__) for type_ in types)
            msg = (
                f"Found a channel of type {type(channel).__name__!r} for id"
                f" {argument!r}, expected (any of) type(s) {type_str}."
            )
            raise TypeError(msg)

        return typing.cast(_ChannelT, channel)

    return base.Parser.from_funcs(
        _fetch_channel,
        snowflake.snowflake_dumps,
        is_default_for=is_default_for or types,
    )


# ASYNC ABSTRACT

GuildChannelParser = _build_async_channel_parser(disnake.abc.GuildChannel)
PrivateChannelParser = _build_async_channel_parser(disnake.abc.PrivateChannel)


# ASYNC PRIVATE

DMChannelParser = _build_async_channel_parser(disnake.DMChannel)
GroupChannelParser = _build_async_channel_parser(disnake.GroupChannel)


# ASYNC GUILD

ForumChannelParser = _build_async_channel_parser(disnake.ForumChannel)
NewsChannelParser = _build_async_channel_parser(disnake.NewsChannel)
VoiceChannelParser = _build_async_channel_parser(disnake.VoiceChannel)
StageChannelParser = _build_async_channel_parser(disnake.StageChannel)
TextChannelParser = _build_async_channel_parser(disnake.TextChannel)
ThreadParser = _build_async_channel_parser(disnake.Thread)
CategoryParser = _build_async_channel_parser(disnake.CategoryChannel)


class PartialMessageableParser(  # noqa: D101
    base.Parser[disnake.PartialMessageable],
    is_default_for=(disnake.PartialMessageable,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(
        self, channel_type: typing.Optional[disnake.ChannelType] = None
    ) -> None:
        self.channel_type = channel_type
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.PartialMessageable:
        # <<docstring inherited from parser_api.Parser>>

        return inter.bot.get_partial_messageable(int(argument), type=self.channel_type)
