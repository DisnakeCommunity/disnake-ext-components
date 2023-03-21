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


def _get_message(inter: disnake.Interaction, argument: str) -> disnake.Message:
    message = inter.bot.get_message(int(argument))

    if message is None:
        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)

    return message


async def _fetch_message(inter: disnake.Interaction, argument: str) -> disnake.Message:
    return await inter.channel.fetch_message(int(argument))


GetMessageParser = base.Parser.from_funcs(
    _get_message, snowflake.snowflake_dumps, is_default_for=(disnake.Message,)
)
MessageParser = base.Parser.from_funcs(
    _fetch_message, snowflake.snowflake_dumps, is_default_for=(disnake.Message,)
)
PartialMessageParser = base.Parser.from_funcs(
    lambda inter, argument: disnake.PartialMessage(
        channel=inter.channel, id=int(argument)
    ),
    snowflake.snowflake_dumps,
    is_default_for=(disnake.PartialMessage,),
)
