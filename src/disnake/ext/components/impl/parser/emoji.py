"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetEmojiParser",
    "EmojiParser",
    "PartialEmojiParser",
    "GetStickerParser",
    "StickerParser",
)


# GET_ONLY


def _get_emoji(inter: disnake.Interaction, argument: str) -> disnake.Emoji:
    emoji = inter.bot.get_emoji(int(argument))

    if emoji is None:
        msg = f"Could not find an emoji with id {argument!r}."
        raise LookupError(msg)

    return emoji


def _get_sticker(inter: disnake.Interaction, argument: str) -> disnake.Sticker:
    sticker = inter.bot.get_sticker(int(argument))

    if sticker is None:
        msg = f"Could not find an emoji with id {argument!r}."
        raise LookupError(msg)

    return sticker


# GET AND FETCH


async def _fetch_emoji(inter: disnake.Interaction, argument: str) -> disnake.Emoji:
    if inter.guild is None:
        msg = (
            "Impossible to fetch an emoji from an "
            "interaction that doesn't come from a guild."
        )
        raise TypeError(msg)
    return (
        inter.bot.get_emoji(int(argument))
        or await inter.guild.fetch_emoji(int(argument))
    )  # fmt: skip


async def _fetch_sticker(inter: disnake.Interaction, argument: str) -> disnake.Sticker:
    if inter.guild is None:
        msg = (
            "Impossible to fetch a sticker from an "
            "interaction that doesn't come from a guild."
        )
        raise TypeError(msg)
    return (
        inter.bot.get_sticker(int(argument))
        or await inter.guild.fetch_sticker(int(argument))
    )  # fmt: skip


GetEmojiParser = base.Parser.from_funcs(
    _get_emoji, snowflake.snowflake_dumps, is_default_for=(disnake.Emoji,)
)
GetStickerParser = base.Parser.from_funcs(
    _get_sticker, snowflake.snowflake_dumps, is_default_for=(disnake.Sticker,)
)


EmojiParser = base.Parser.from_funcs(
    _fetch_emoji, snowflake.snowflake_dumps, is_default_for=(disnake.Emoji,)
)
PartialEmojiParser = base.Parser.from_funcs(
    lambda _, argument: disnake.PartialEmoji.from_dict({"id": int(argument)}),
    lambda argument: str(argument.id),
    is_default_for=(disnake.PartialEmoji,),
)
StickerParser = base.Parser.from_funcs(
    _fetch_sticker, snowflake.snowflake_dumps, is_default_for=(disnake.Sticker,)
)
