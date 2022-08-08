from __future__ import annotations

import typing as t

import disnake
import pytest

import disnake_ext_components as components


def dummy_sync_check(inter: disnake.MessageInteraction) -> bool:
    return inter.component.custom_id == "success"


async def dummy_async_check(inter: disnake.MessageInteraction) -> bool:
    return inter.component.custom_id == "success"


@pytest.fixture()
def listener():
    @components.button_listener()
    async def dummy_listener(inter: disnake.MessageInteraction):
        ...

    return dummy_listener


# abc.BaseListener.add_check


@pytest.mark.asyncio()
async def test_add_check(listener: components.SelectListener[t.Any, t.Any]):

    listener.add_check(dummy_sync_check)

    assert listener.checks[0] is dummy_sync_check

    listener.add_check(dummy_async_check)

    assert listener.checks[1] is dummy_async_check


# utils.assert_all_checks


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("custom_id", "expected", "checks"),
    [
        ("success", True, [dummy_sync_check]),
        ("failure", False, [dummy_async_check]),
        ("success", True, [dummy_sync_check, dummy_async_check]),
        ("failure", False, [dummy_sync_check, dummy_async_check]),
    ],
)
async def test_sync_check(
    listener: components.SelectListener[t.Any, t.Any],
    msg_inter: disnake.MessageInteraction,
    custom_id: str,
    expected: bool,
    checks: t.Sequence[t.Callable[..., t.Any]],
):
    for check in checks:
        listener.add_check(check)

    msg_inter.component.custom_id = custom_id
    assert expected is await components.utils.assert_all_checks(listener.checks, msg_inter)


# utils.build_component_matching_check


b = disnake.ui.Button[t.Any]
s = disnake.ui.Select[t.Any]
bs = disnake.ButtonStyle


@pytest.mark.parametrize(
    ("componentA", "componentB", "kwargsA", "kwargsB", "expected"),
    [
        # Check all individual params...
        # Note that custom_id must be set for comparison, otherwise disnake will randomly
        # generate them, and they won't match.
        (b, b, {"custom_id": "abc"},                       {"custom_id": "abc"},                            True),
        (s, s, {"custom_id": "abc"},                       {"custom_id": "abc"},                            True),
        (b, s, {"custom_id": "abc"},                       {"custom_id": "abc"},                            False),

        (b, b, {"custom_id": "abc", "disabled": True},     {"custom_id": "abc", "disabled": True},          True),
        (s, s, {"custom_id": "abc", "disabled": True},     {"custom_id": "abc", "disabled": True},          True),
        (b, s, {"custom_id": "abc", "disabled": True},     {"custom_id": "abc", "disabled": True},          False),

        (b, b, {"custom_id": "abc", "label": "abc"},       {"custom_id": "abc", "label": "abc"},            True),
        (b, b, {"custom_id": "abc", "label": "abc"},       {"custom_id": "abc", "label": "def"},            False),

        (b, b, {"custom_id": "abc", "emoji": "abc"},       {"custom_id": "abc", "emoji": "abc"},            True),
        (b, b, {"custom_id": "abc", "emoji": "abc"},       {"custom_id": "abc", "emoji": "def"},            False),

        (b, b, {"custom_id": "abc", "style": bs.red},      {"custom_id": "abc", "style": bs.red},           True),
        (b, b, {"custom_id": "abc", "style": bs.red},      {"custom_id": "abc", "style": bs.gray},          False),

        (s, s, {"custom_id": "abc", "max_values": 6},      {"custom_id": "abc", "max_values": 6},           True),
        (s, s, {"custom_id": "abc", "max_values": 6},      {"custom_id": "abc", "max_values": 9},           False),

        (s, s, {"custom_id": "abc", "min_values": 6},      {"custom_id": "abc", "min_values": 6},           True),
        (s, s, {"custom_id": "abc", "min_values": 6},      {"custom_id": "abc", "min_values": 9},           False),

        (s, s, {"custom_id": "abc", "placeholder": "abc"}, {"custom_id": "abc", "placeholder": "abc"},      True),
        (s, s, {"custom_id": "abc", "placeholder": "abc"}, {"custom_id": "abc", "placeholder": "def"},      False),

        (s, s, {"custom_id": "abc", "options": ["abc"]},   {"custom_id": "abc", "options": ["abc"]},        True),
        (s, s, {"custom_id": "abc", "options": ["abc"]},   {"custom_id": "abc", "options": ["def"]},        False),
        (s, s, {"custom_id": "abc", "options": ["abc"]},   {"custom_id": "abc", "options": ["abc", "def"]}, False),
        (s, s, {"custom_id": "abc", "options": ["abc"]},   {"custom_id": "abc", "options": {"abc": "def"}}, False),

        # Confirm that supersets aren't allowed...
        (b, b, {"custom_id": "abc"},                       {"custom_id": "abc", "label": "abc"},            False),
        (s, s, {"custom_id": "abc"},                       {"custom_id": "abc", "placeholder": "abc"},      False),
    ],  # fmt: skip
)
def test_build_component_matching_check_component(
    componentA: t.Union[t.Type[b], t.Type[s]],
    componentB: t.Union[t.Type[b], t.Type[s]],
    kwargsA: t.Dict[str, t.Any],
    kwargsB: t.Dict[str, t.Any],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    actualA = componentA(**kwargsA)
    actualB = componentB(**kwargsB)
    check = components.utils.build_component_matching_check(actualA)

    msg_inter.component = actualB._underlying  # type: ignore

    assert check(msg_inter) is expected


@pytest.mark.parametrize(
    ("kwargs", "component", "expected"),
    [
        # Check all individual params...
        # Note that custom_id must be set for comparison, otherwise disnake will randomly
        # generate them, and they won't match.
        ({"custom_id": "abc"},                       b(custom_id="abc"),                         True),
        ({"custom_id": "abc"},                       s(custom_id="abc"),                         True),
        ({"custom_id": "abc"},                       b(custom_id="def"),                         False),

        ({"custom_id": "abc", "disabled": True},     b(custom_id="abc", disabled=True),          True),
        ({"custom_id": "abc", "disabled": True},     s(custom_id="abc", disabled=True),          True),
        ({"custom_id": "abc", "disabled": True},     b(custom_id="abc", disabled=False),         False),

        ({"custom_id": "abc", "label": "abc"},       b(custom_id="abc", label="abc"),            True),
        ({"custom_id": "abc", "label": "abc"},       b(custom_id="abc", label="def"),            False),

        ({"custom_id": "abc", "emoji": "abc"},       b(custom_id="abc", emoji="abc"),            True),
        ({"custom_id": "abc", "emoji": "abc"},       b(custom_id="abc", emoji="def"),            False),

        ({"custom_id": "abc", "style": bs.red},      b(custom_id="abc", style=bs.red),           True),
        ({"custom_id": "abc", "style": bs.red},      b(custom_id="abc", style=bs.gray),          False),

        ({"custom_id": "abc", "max_values": 6},      s(custom_id="abc", max_values=6),           True),
        ({"custom_id": "abc", "max_values": 6},      s(custom_id="abc", max_values=9),           False),

        ({"custom_id": "abc", "min_values": 6},      s(custom_id="abc", min_values=6),           True),
        ({"custom_id": "abc", "min_values": 6},      s(custom_id="abc", min_values=9),           False),

        ({"custom_id": "abc", "placeholder": "abc"}, s(custom_id="abc", placeholder="abc"),      True),
        ({"custom_id": "abc", "placeholder": "abc"}, s(custom_id="abc", placeholder="def"),      False),

        ({"custom_id": "abc", "options": ["abc"]},   s(custom_id="abc", options=["abc"]),        True),
        ({"custom_id": "abc", "options": ["abc"]},   s(custom_id="abc", options=["def"]),        False),
        ({"custom_id": "abc", "options": ["abc"]},   s(custom_id="abc", options=["abc", "def"]), False),
        ({"custom_id": "abc", "options": ["abc"]},   s(custom_id="abc", options={"abc": "def"}), False),

        # Confirm that supersets are allowed...
        ({"custom_id": "abc"},                       b(custom_id="abc", label="abc"),            True),
        ({"custom_id": "abc"},                       s(custom_id="abc", placeholder="abc"),      True),
    ],  # fmt: skip
)
def test_build_component_matching_check_kwargs(  # This should match 'supersets'.
    kwargs: t.Dict[str, t.Any],
    component: t.Union[b, s],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    check = components.utils.build_component_matching_check(**kwargs)
    msg_inter.component = component._underlying  # type: ignore

    assert check(msg_inter) is expected


# listener.match_component

# This may need to be moved to an eventual test_listeners.py.
# Note that a listener just returns early if it fails to match (for now?).


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("componentA", "componentB", "expected"),
    [
        (b(label="abc", custom_id="def"), b(label="abc", custom_id="def"), True),
        (b(label="abc", custom_id="def"), b(label="abc", custom_id="abc"), None),
        (s(custom_id="def"), s(custom_id="def"), True),
        (s(custom_id="def"), s(custom_id="abc"), None),
    ],
)
async def test_match_component_with_component(
    componentA: t.Union[b, s],
    componentB: t.Union[b, s],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    @components.match_component(componentA)
    async def listener(inter: disnake.MessageInteraction) -> bool:
        return True

    msg_inter.component = componentB._underlying  # type: ignore

    assert await listener(msg_inter) is expected


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("kwargs", "component", "expected"),
    [
        ({"custom_id": "abc", "component_type": disnake.ComponentType.button}, b(custom_id="abc"), True),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.button}, s(custom_id="abc"), None),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.select}, b(custom_id="abc"), None),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.select}, s(custom_id="abc"), True),
    ],  # fmt: skip
)
async def test_match_component_with_kwargs(
    kwargs: t.Dict[str, t.Any],
    component: t.Union[b, s],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    @components.match_component(**kwargs)
    async def listener(inter: disnake.MessageInteraction) -> bool:
        return True

    msg_inter.component = component._underlying  # type: ignore

    assert await listener(msg_inter) is expected
