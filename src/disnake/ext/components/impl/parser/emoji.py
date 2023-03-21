"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetEmojiParser",
    "EmojiParser",
    "PartialEmojiParser",
)


def _get_emoji(inter: disnake.Interaction, argument: str) -> disnake.Emoji:
    emoji = inter.bot.get_emoji(int(argument))

    if emoji is None:
        msg = f"Could not find an emoji with id {argument!r}."
        raise LookupError(msg)

    return emoji


async def _fetch_emoji(inter: disnake.Interaction, argument: str) -> disnake.Emoji:
    guild = typing.cast(disnake.Guild, inter.guild)
    return await guild.fetch_emoji(int(argument))


GetEmojiParser = base.Parser.from_funcs(
    _get_emoji, snowflake.snowflake_dumps, is_default_for=(disnake.Emoji,)
)
EmojiParser = base.Parser.from_funcs(
    _fetch_emoji, snowflake.snowflake_dumps, is_default_for=(disnake.Emoji,)
)
PartialEmojiParser = base.Parser.from_funcs(
    lambda _, argument: disnake.PartialEmoji.from_dict({"id": int(argument)}),
    lambda argument: str(argument.id),
    is_default_for=(disnake.PartialEmoji,),
)
