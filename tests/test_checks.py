import typing as t

import disnake
import pytest

import disnake_ext_components as components


def dummy_sync_check(inter: disnake.MessageInteraction) -> bool:
    return inter.component.custom_id == "success"


async def dummy_async_check(inter: disnake.MessageInteraction) -> bool:
    return inter.component.custom_id == "success"


@pytest.fixture
def listener():
    @components.button_listener()
    async def dummy_listener(inter: disnake.MessageInteraction):
        ...

    return dummy_listener


# abc.BaseListener.add_check


@pytest.mark.asyncio
async def test_add_check(listener: components.SelectListener[t.Any, t.Any]):

    listener.add_check(dummy_sync_check)

    assert listener.checks[0] is dummy_sync_check

    listener.add_check(dummy_async_check)

    assert listener.checks[1] is dummy_async_check


# utils.assert_all_checks


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "custom_id, expected, checks",
    (
        ("success", True, [dummy_sync_check]),
        ("failure", False, [dummy_async_check]),
        ("success", True, [dummy_sync_check, dummy_async_check]),
        ("failure", False, [dummy_sync_check, dummy_async_check]),
    ),
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


b = disnake.ui.Button
s = disnake.ui.Select


@pytest.mark.parametrize(
    "componentA, componentB, expected",
    (
        (b(custom_id="abc"), b(custom_id="abc"), True),
        (b(custom_id="abc", label="def"), b(custom_id="abc", label="def"), True),
        # These should fail, as component matching should require an exact match...
        (b(custom_id="abc"), b(custom_id="abc", label="def"), False),
        (b(custom_id="abc", label="def"), b(custom_id="abc"), False),
        (b(custom_id="abc"), b(custom_id="def"), False),
        # Same checks with selects for good measure...
        (s(custom_id="abc"), s(custom_id="abc"), True),
        (s(custom_id="abc"), s(custom_id="abc", placeholder="def"), False),
        (s(custom_id="abc", placeholder="def"), s(custom_id="abc"), False),
        (s(custom_id="abc"), s(custom_id="def"), False),
        (s(custom_id="abc", placeholder="def"), s(custom_id="abc", placeholder="def"), True),
        # Ensure component types match...
        (s(custom_id="abc"), b(custom_id="abc"), False),
    ),
)
def test_build_component_matching_check_component(
    componentA: t.Union[b[t.Any], s[t.Any]],
    componentB: t.Union[b[t.Any], s[t.Any]],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    check = components.utils.build_component_matching_check(componentA)
    msg_inter.component = componentB._underlying  # type: ignore

    assert check(msg_inter) is expected


@pytest.mark.parametrize(
    "kwargs, component, expected",
    (
        # These should succeed, as partial matching should succeed as long as the provided
        # component matches at least the provided kwargs; the rest can be anything.
        # Note that, since no type is provided, both buttons and selects will work.
        ({"custom_id": "abc"}, b(custom_id="abc"), True),
        ({"custom_id": "abc"}, s(custom_id="abc"), True),
        ({"custom_id": "abc"}, b(custom_id="abc", label="def"), True),
        ({"custom_id": "abc", "label": "def"}, b(custom_id="abc", label="def"), True),
        # These should fail, as described above.
        ({"custom_id": "abc", "label": "def"}, b(custom_id="abc"), False),
        ({"custom_id": "abc", "label": "def"}, s(custom_id="abc"), False),
        ({"custom_id": "abc"}, b(custom_id="def"), False),
        ({"custom_id": "abc"}, s(custom_id="def"), False),
        # Now setting type...
        ({"custom_id": "abc", "type": disnake.ComponentType.button}, b(custom_id="abc"), True),
        ({"custom_id": "abc", "type": disnake.ComponentType.button}, s(custom_id="abc"), False),
        ({"custom_id": "abc", "type": disnake.ComponentType.select}, b(custom_id="abc"), False),
        ({"custom_id": "abc", "type": disnake.ComponentType.select}, s(custom_id="abc"), True),
    ),
)
def test_build_component_matching_check_kwargs(  # This should match 'supersets'.
    kwargs: t.Dict[str, t.Any],
    component: t.Union[b[t.Any], s[t.Any]],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    check = components.utils.build_component_matching_check(**kwargs)
    msg_inter.component = component._underlying  # type: ignore

    assert check(msg_inter) is expected


# listener.match_component

# This may need to be moved to an eventual test_listeners.py.
# Note that a listener just returns early if it fails to match (for now?).


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "componentA, componentB, expected",
    (
        (b(label="abc", custom_id="def"), b(label="abc", custom_id="def"), True),
        (b(label="abc", custom_id="def"), b(label="abc", custom_id="abc"), None),
        (s(custom_id="def"), s(custom_id="def"), True),
        (s(custom_id="def"), s(custom_id="abc"), None),
    ),
)
async def test_match_component_with_component(
    componentA: t.Union[b[t.Any], s[t.Any]],
    componentB: t.Union[b[t.Any], s[t.Any]],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    @components.match_component(componentA)
    async def listener(inter: disnake.MessageInteraction) -> bool:
        return True

    msg_inter.component = componentB._underlying  # type: ignore

    assert await listener(msg_inter) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs, component, expected",
    (
        ({"custom_id": "abc", "component_type": disnake.ComponentType.button}, b(custom_id="abc"), True),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.button}, s(custom_id="abc"), None),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.select}, b(custom_id="abc"), None),
        ({"custom_id": "abc", "component_type": disnake.ComponentType.select}, s(custom_id="abc"), True),
    ),  # fmt: skip
)
async def test_match_component_with_kwargs(
    kwargs: t.Dict[str, t.Any],
    component: t.Union[b[t.Any], s[t.Any]],
    expected: bool,
    msg_inter: disnake.MessageInteraction,
):
    @components.match_component(**kwargs)
    async def listener(inter: disnake.MessageInteraction) -> bool:
        return True

    msg_inter.component = component._underlying  # type: ignore

    assert await listener(msg_inter) is expected
