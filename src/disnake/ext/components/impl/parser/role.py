"""Parser implementations for disnake role types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetRoleParser",
    "RoleParser",
)


def _get_role(inter: disnake.Interaction, argument: str) -> disnake.Role:
    if inter.guild is None:
        msg = (
            "Impossible to get a role from an"
            "interaction that doesn't come from a guild."
        )
        raise TypeError(msg)
    role = inter.guild.get_role(int(argument))

    if role is None:
        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    return role


async def _fetch_role(inter: disnake.Interaction, argument: str) -> disnake.Role:
    if inter.guild is None:
        msg = (
            "Impossible to fetch a role from an"
            "interaction that doesn't come from a guild."
        )
        raise TypeError(msg)
    role = (
        inter.guild.get_role(int(argument))
        or disnake.utils.get(await inter.guild.fetch_roles(), id=int(argument))
    )  # fmt: skip

    # a role id coming from a custom_id could be of a deleted role object
    # so we're handling that possibility
    if role is None:
        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    return role


GetRoleParser = base.Parser.from_funcs(
    _get_role, snowflake.snowflake_dumps, is_default_for=(disnake.Role,)
)
RoleParser = base.Parser.from_funcs(
    _fetch_role, snowflake.snowflake_dumps, is_default_for=(disnake.Role,)
)
