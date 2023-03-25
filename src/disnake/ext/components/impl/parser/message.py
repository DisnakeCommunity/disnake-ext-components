"""Parser implementations for disnake message types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetMessageParser",
    "MessageParser",
    "PartialMessageParser",
)

AnyChannel = typing.Union[
    disnake.abc.GuildMessageable,  # type: ignore[reportPrivateImportUsage]
    disnake.DMChannel,
    disnake.PartialMessageable,
]


def _get_message(inter: disnake.Interaction, argument: str) -> disnake.Message:
    message = inter.bot.get_message(int(argument))

    if message is None:
        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)

    return message


async def _fetch_message(inter: disnake.Interaction, argument: str) -> disnake.Message:
    return (
        inter.bot.get_message(int(argument))
        or await inter.channel.fetch_message(int(argument))
    )  # fmt: skip


GetMessageParser = base.Parser.from_funcs(
    _get_message, snowflake.snowflake_dumps, is_default_for=(disnake.Message,)
)
MessageParser = base.Parser.from_funcs(
    _fetch_message, snowflake.snowflake_dumps, is_default_for=(disnake.Message,)
)


class PartialMessageParser(  # noqa: D101
    base.Parser, is_default_for=(disnake.PartialMessage,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self, channel: typing.Optional[AnyChannel] = None) -> None:
        self.channel = channel
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.PartialMessage:
        # <<docstring inherited from parser_api.Parser>>

        return disnake.PartialMessage(channel=inter.channel, id=int(argument))
