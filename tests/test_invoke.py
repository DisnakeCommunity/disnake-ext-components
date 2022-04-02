import disnake
import pytest
from disnake.ext import commands, components


@pytest.fixture
def default_listener():
    class A(commands.Cog):
        @components.component_listener(sep="<>")
        async def default_listener(self, inter: disnake.MessageInteraction, int_: int):
            return int_

    return A().default_listener


@pytest.fixture
def regex_listener():
    class A(commands.Cog):
        @components.component_listener(regex=r"custom_regex:(?P<int_>.+)")
        async def regex_listener(self, inter: disnake.MessageInteraction, int_: int):
            return int_

    return A().regex_listener


async def test_invoke_default_pass(default_listener, inter):
    """Test a default listener with correct invocations."""

    x = "passed_as_is"
    inter.component.custom_id = "should_get_skipped_anyways"
    assert await default_listener(inter, x) is x

    inter.component.custom_id = "default_listener<>123"
    assert await default_listener(inter) == 123


async def test_invoke_default_ignore(default_listener, inter):
    """Test a default listener invocation that is ignored becuase of a name mismatch."""

    inter.component.custom_id = "blatantly_wrong"
    assert await default_listener(inter) is None


async def test_invoke_default_fail(default_listener, inter):
    """Test a default listener invocation that fails during param conversion."""

    inter.component.custom_id = "default_listener<>abc"
    with pytest.raises(components.exceptions.ConversionError) as exc_info:
        await default_listener(inter)

    assert isinstance(exc_info.value.exceptions[0], components.exceptions.MatchFailure)


async def test_invoke_regex_pass(regex_listener, inter):
    """Test a default listener with correct invocations."""

    x = "passed_as_is"
    inter.component.custom_id = "should_get_skipped_anyways"
    assert await regex_listener(inter, x) is x

    inter.component.custom_id = "custom_regex:123"
    assert await regex_listener(inter) == 123


async def test_invoke_regex_ignore(regex_listener, inter):
    inter.component.custom_id = "__custom_regex:123"
    assert await regex_listener(inter) is None


async def test_invoke_regex_fail(regex_listener, inter):
    """Test a regex listener invocation that fails during param conversion."""

    inter.component.custom_id = "custom_regex:abc"
    with pytest.raises(components.exceptions.ConversionError) as exc_info:
        await regex_listener(inter)

    assert isinstance(exc_info.value.exceptions[0], commands.BadArgument)
