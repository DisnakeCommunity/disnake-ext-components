import typing as t

import disnake
import pytest

import disnake_ext_components as components


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "component, overrides, expected",
    (
        # Note that we *need* to set custom ids here for validation, as disnake will otherwise
        # generate random ones for us. This will cause a mismatch between the created component
        # and the one with which we wish to validate it.
        (disnake.ui.Button(custom_id="abc"), {},                     disnake.ui.Button(custom_id="abc")),
        (disnake.ui.Select(custom_id="abc"), {},                     disnake.ui.Select(custom_id="abc")),
        (disnake.ui.Button(custom_id="abc"), {"label": "def"},       disnake.ui.Button(custom_id="abc", label="def")),
        (disnake.ui.Select(custom_id="abc"), {"placeholder": "def"}, disnake.ui.Select(custom_id="abc", placeholder="def")),
        # Ensure overwriting attributes works..
        (disnake.ui.Button(custom_id="abc", label="abc"),       {"label": "def"},       disnake.ui.Button(custom_id="abc", label="def")),
        (disnake.ui.Select(custom_id="abc", placeholder="abc"), {"placeholder": "def"}, disnake.ui.Select(custom_id="abc", placeholder="def")),
    )  # fmt: skip
)
async def test_build_from_component(
    component: t.Union[disnake.ui.Button[t.Any], disnake.ui.Select[t.Any]],
    overrides: t.Dict[str, t.Any],
    expected: t.Union[disnake.ui.Button[t.Any], disnake.ui.Select[t.Any]],
):
    @components.match_component(component)
    async def listener(inter: disnake.MessageInteraction):
        ...

    built = await listener.build_component(**overrides)
    assert built.to_component_dict() == expected.to_component_dict()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs, overrides, expected",
    (
        ({"component_type": disnake.ComponentType.button, "custom_id": "abc"}, {},                     disnake.ui.Button(custom_id="abc")),
        ({"component_type": disnake.ComponentType.select, "custom_id": "abc"}, {},                     disnake.ui.Select(custom_id="abc")),
        ({"component_type": disnake.ComponentType.button, "custom_id": "abc"}, {"label": "def"},       disnake.ui.Button(custom_id="abc", label="def")),
        ({"component_type": disnake.ComponentType.select, "custom_id": "abc"}, {"placeholder": "def"}, disnake.ui.Select(custom_id="abc", placeholder="def")),
        # # Ensure overwriting attributes works..
        ({"component_type": disnake.ComponentType.button, "custom_id": "abc", "label": "abc"},       {"label": "def"},       disnake.ui.Button(custom_id="abc", label="def")),
        ({"component_type": disnake.ComponentType.select, "custom_id": "abc", "placeholder": "abc"}, {"placeholder": "def"}, disnake.ui.Select(custom_id="abc", placeholder="def")),
    )  # fmt: skip
)
async def test_build_from_kwargs(
    kwargs: t.Dict[str, t.Any],
    overrides: t.Dict[str, t.Any],
    expected: t.Union[disnake.ui.Button[t.Any], disnake.ui.Select[t.Any]],
):
    @components.match_component(**kwargs)
    async def listener(inter: disnake.MessageInteraction):
        ...

    built = await listener.build_component(**overrides)
    assert built.to_component_dict() == expected.to_component_dict()
