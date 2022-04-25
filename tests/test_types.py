import typing as t

import disnake
import pytest
from disnake.ext import commands

import disnake_ext_components as components


@pytest.mark.asyncio
async def test_int():
    """Test a listener with int params."""

    class A(commands.Cog):
        @components.button_listener()
        async def int_listener(
            self, inter: disnake.MessageInteraction, int_: int, int_with_default: int = 3
        ):
            ...

    actual = A().int_listener

    assert actual.id_spec == "int_listener:{int_}:{int_with_default}"

    params = actual.params

    assert await params[0].convert("123", inter=None) == 123
    assert await params[0].convert("-123", inter=None) == -123

    with pytest.raises(components.exceptions.ConversionError):
        await params[0].convert("1.23", inter=None)

    assert await params[1].convert("123", inter=None) == 123
    assert await params[1].convert("1.23", inter=None) == 3


@pytest.mark.asyncio
async def test_bool():
    """Test a listener with bool param."""

    class A(commands.Cog):
        @components.button_listener(sep=":")
        async def bool_listener(self, inter: disnake.MessageInteraction, bool_: bool):
            ...

    actual = A().bool_listener
    param = actual.params[0]
    trues = ["true", "t", "yes", "y", "1", "enable", "on"]
    falses = ["false", "f", "no", "n", "0", "disable", "off"]

    assert all([await param.convert(true, inter=None) is True for true in trues])
    assert all([await param.convert(false, inter=None) is False for false in falses])

    with pytest.raises(components.exceptions.ConversionError):
        await param.convert("1.23", inter=None)


@pytest.mark.asyncio
async def test_unannotated():
    """Test a listener with unannotated param."""

    class A(commands.Cog):
        @components.button_listener(sep=":")
        async def unannotated_listener(
            self, inter: disnake.MessageInteraction, please_use_typehints
        ):
            ...

    actual = A().unannotated_listener
    param = actual.params[0]
    assert await param.convert("pretty please", inter=None) == "pretty please"


@pytest.mark.asyncio
async def test_union():
    """Test a listener with union param."""

    class A(commands.Cog):
        @components.button_listener(sep=":")
        async def union_listener(
            self, inter: disnake.MessageInteraction, int_or_bool: t.Union[int, bool]
        ):
            ...

    actual = A().union_listener
    param = actual.params[0]

    assert await param.convert("123", inter=None) == 123
    assert await param.convert("true", inter=None) is True

    with pytest.raises(components.exceptions.ConversionError):
        await param.convert("abc", inter=None)


@pytest.mark.asyncio
async def test_optional():
    """Test a listener with optional param."""

    class A(commands.Cog):
        @components.button_listener(sep=":")
        async def optional_listener(
            self, inter: disnake.MessageInteraction, optional: t.Optional[int]
        ):
            ...

    actual = A().optional_listener
    param = actual.params[0]

    assert await param.convert("123", inter=None) == 123
    assert await param.convert("true", inter=None) is None


@pytest.mark.asyncio
async def test_literal():
    """Test a listener with literal param."""

    class A(commands.Cog):
        @components.button_listener(sep=":")
        async def literal_listener(
            self, inter: disnake.MessageInteraction, literal: t.Literal["sheesh", 123, True]
        ):
            ...

    actual = A().literal_listener
    param = actual.params[0]

    assert await param.convert("sheesh", inter=None) == "sheesh"
    assert await param.convert("123", inter=None) == 123
    assert await param.convert("True", inter=None) is True

    with pytest.raises(components.exceptions.ConversionError):
        await param.convert("something dumb", inter=None)
