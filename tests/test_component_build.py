import typing as t

import disnake
import pytest

import disnake_ext_components as components


b = disnake.ui.Button[t.Any]
s = disnake.ui.Select[t.Any]
ct = disnake.ComponentType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "component, overrides, expected",
    (
        # Note that we *need* to set custom ids here for validation, as disnake will otherwise
        # generate random ones for us. This will cause a mismatch between the created component
        # and the one with which we wish to validate it.
        (b(custom_id="abc"),                    {},                     b(custom_id="abc")),
        (s(custom_id="abc"),                    {},                     s(custom_id="abc")),
        (b(custom_id="abc"),                    {"label": "def"},       b(custom_id="abc", label="def")),
        (s(custom_id="abc"),                    {"placeholder": "def"}, s(custom_id="abc", placeholder="def")),
        # Ensure overwriting attributes works..
        (b(custom_id="abc", label="abc"),       {"label": "def"},       b(custom_id="abc", label="def")),
        (s(custom_id="abc", placeholder="abc"), {"placeholder": "def"}, s(custom_id="abc", placeholder="def")),
    )  # fmt: skip
)
async def test_build_from_component(
    component: t.Union[b, s],
    overrides: t.Dict[str, t.Any],
    expected: t.Union[b, s],
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
        ({"component_type": ct.button, "custom_id": "abc"}, {},                     b(custom_id="abc")),
        ({"component_type": ct.select, "custom_id": "abc"}, {},                     s(custom_id="abc")),
        ({"component_type": ct.button, "custom_id": "abc"}, {"label": "def"},       b(custom_id="abc", label="def")),
        ({"component_type": ct.select, "custom_id": "abc"}, {"placeholder": "def"}, s(custom_id="abc", placeholder="def")),
        # # Ensure overwriting attributes works..
        ({"component_type": ct.button, "custom_id": "abc", "label": "abc"},       {"label": "def"},       b(custom_id="abc", label="def")),
        ({"component_type": ct.select, "custom_id": "abc", "placeholder": "abc"}, {"placeholder": "def"}, s(custom_id="abc", placeholder="def")),
    )  # fmt: skip
)
async def test_build_from_kwargs(
    kwargs: t.Dict[str, t.Any],
    overrides: t.Dict[str, t.Any],
    expected: t.Union[b, s],
):
    @components.match_component(**kwargs)
    async def listener(inter: disnake.MessageInteraction):
        ...

    built = await listener.build_component(**overrides)
    assert built.to_component_dict() == expected.to_component_dict()
