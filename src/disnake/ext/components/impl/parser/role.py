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
    guild = typing.cast(disnake.Guild, inter.guild)
    role = guild.get_role(int(argument))

    if role is None:
        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    return role


async def _fetch_role(inter: disnake.Interaction, argument: str) -> disnake.Role:
    # same problem as user.py with all these cast
    guild = typing.cast(disnake.Guild, inter.guild)
    role = (
        guild.get_role(int(argument))
        or disnake.utils.get(await guild.fetch_roles(), id=int(argument))
    )

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
