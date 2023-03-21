"""Parser implementations for disnake permissions types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base

__all__: typing.Sequence[str] = ("PermissionsParser",)


PermissionsParser = base.Parser.from_funcs(
    lambda _, argument: disnake.Permissions(int(argument)),
    lambda argument: str(argument.value),
    is_default_for=(disnake.Permissions,),
)
