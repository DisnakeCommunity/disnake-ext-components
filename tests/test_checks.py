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


# abc.Listener.add_check


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
