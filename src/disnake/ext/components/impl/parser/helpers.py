"""Module with helper protocols for parser source object annotations."""

import typing

import disnake
from disnake.ext import commands

_AnyBot = typing.Union[
    commands.Bot,
    commands.InteractionBot,
    commands.AutoShardedBot,
    commands.AutoShardedInteractionBot,
]
_AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


@typing.runtime_checkable
class BotAware(typing.Protocol):
    """Protocol for a class that contains a reference to the bot."""

    @property
    def bot(self) -> _AnyBot:  # noqa: D102
        ...


@typing.runtime_checkable
class GuildAware(typing.Protocol):
    """Protocol for a class that contains a reference to a guild."""

    @property
    def guild(self) -> typing.Optional[disnake.Guild]:  # noqa: D102
        ...


@typing.runtime_checkable
class MessageAware(typing.Protocol):
    """Protocol for a class that contains a reference to a message."""

    @property
    def message(self) -> disnake.Message:  # noqa: D102
        ...


@typing.runtime_checkable
class ChannelAware(typing.Protocol):
    """Protocol for a class that contains a reference to a channel."""

    @property
    def channel(self) -> _AnyChannel:  # noqa: D102
        ...


class BotAndGuildAware(BotAware, GuildAware, typing.Protocol):
    """Protocol for a class that contains a refernce to the bot and a guild."""
