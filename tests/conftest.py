import typing as t
from unittest import mock

import disnake
import pytest

import disnake_ext_components as components


@pytest.fixture()
def msg_inter():
    return mock.Mock(spec=disnake.MessageInteraction)


@pytest.fixture()
def modal_inter():
    return mock.Mock(spec=disnake.MessageInteraction)


@pytest.fixture()
def button_listener_callback():
    async def button_listener_callback(inter: disnake.MessageInteraction, *, foo: int, bar: str):
        ...

    return button_listener_callback


@pytest.fixture()
def select_listener_callback():
    async def select_listener_callback(
        inter: disnake.MessageInteraction,
        selected: t.List[str] = components.SelectValue("bean"),
        *,
        foo: int,
        bar: str,
    ):
        ...

    return select_listener_callback


@pytest.fixture()
def modal_listener_callback():
    async def modal_listener_callback(
        inter: disnake.MessageInteraction,
        field_A: t.List[str] = components.ModalValue("bean"),
        field_B: t.List[str] = components.ParagraphModalValue("bean"),
        *,
        foo: int,
        bar: str,
    ):
        ...

    return modal_listener_callback
