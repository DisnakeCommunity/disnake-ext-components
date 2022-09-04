# TODO: Add more tests to ensure proper functionality before pypi release!

import typing as t

import disnake
import pytest

import disnake_ext_components as components
from disnake_ext_components import abc

# The decorated function...
ListenerCallback = t.Callable[..., t.Any]

# The return type of the wrapped decorator...
# (callable that should take the decorated func and return a listener)
WrappedCallback = t.Callable[[ListenerCallback], abc.BaseListener[t.Any, t.Any, t.Any]]

# The decorator itself...
# (callable that should take args, then return the above decorator)
ListenerBuilder = t.Callable[..., WrappedCallback]


@pytest.mark.parametrize(
    "listener_decorator",
    [components.button_listener, components.select_listener],
)
def test_listener_name_default(listener_decorator: ListenerBuilder):
    # Simple listeners should infer their name from the callback by default...

    @listener_decorator()
    async def callback(inter: disnake.MessageInteraction):
        pass

    assert callback.name == "callback"


def test_listener_name_default_modal():
    # Modals need a ModalInteraction and at least one textinput field...

    @components.modal_listener()
    async def callback(inter: disnake.ModalInteraction, field1: str):
        pass

    assert callback.name == "callback"


@pytest.mark.parametrize(
    "listener_decorator",
    [components.button_listener, components.select_listener],
)
def test_listener_name_override(listener_decorator: ListenerBuilder):

    override = "make_sure_this_is_overwritten"

    @listener_decorator(name=override)
    async def this_should_not_show_up(inter: disnake.MessageInteraction):
        pass

    assert this_should_not_show_up.name == override


def test_listener_name_override_modal():

    override = "make_sure_this_is_overwritten"

    @components.modal_listener(name=override)
    async def this_should_not_show_up(inter: disnake.ModalInteraction, field1: str):
        pass

    assert this_should_not_show_up.name == override


# TODO: Add tests for match_component naming, though that needs some further work.
#       Currently, they allow not specifying a name at all, which I doubt actually
#       offers any useful functionality, and also caused the naming regression.
#
#       I will therefore probably end up slightly reworking match_component first,
#       before continuing with these tests.
