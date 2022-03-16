# TODO: make these work for bot.listen too

import functools
import re
import typing as t

import disnake
from disnake.ext import commands

__all__ = [
    "component_with_id",
    "button_with_id",
    "dropdown_with_id",
    "select_with_id",  # alias
]


class ComponentListenerT(t.Protocol):
    async def __call__(_, self: t.Any, inter: disnake.MessageInteraction, **kwargs):
        ...


def _create_id_wrapper(id: str, func: ComponentListenerT) -> ComponentListenerT:
    if not isinstance(id, str):
        raise TypeError(f"Parameter 'id' expected type str, got {type(id).__name__}")

    async def wrapper(self, inter: disnake.MessageInteraction, **kwargs: t.Any):
        if not (custom_id := inter.component.custom_id):
            return
        if custom_id != id:
            return
        await func(self, inter)

    return wrapper


def _create_regex_wrapper(
    regex: t.Union[re.Pattern, str], func: ComponentListenerT
) -> ComponentListenerT:
    if isinstance(regex, str):
        pattern = re.compile(regex)
    elif isinstance(regex, re.Pattern):
        pattern = regex
    else:
        raise TypeError(
            f"Parameter 'regex' expected type str or re.Pattern, got {type(regex).__name__}."
        )

    async def wrapper(self, inter: disnake.MessageInteraction, **kwargs: t.Any):
        if not (custom_id := inter.component.custom_id):
            return
        if not (match := pattern.fullmatch(custom_id)):
            return
        return await func(self, inter, **match.groupdict())

    return wrapper


def _component_with_id(
    *component_listener_types,
    id: t.Optional[str] = None,
    regex: t.Union[str, re.Pattern, None] = None,
) -> t.Callable[[ComponentListenerT], ComponentListenerT]:
    if not (id is None) ^ (regex is None):
        raise ValueError("Exactly one of parameters 'id' and 'regex' should be set.")

    def decorator(func: ComponentListenerT):
        if id:
            wrapper = _create_id_wrapper(id, func)
        elif regex:
            wrapper = _create_regex_wrapper(regex, func)

        for listener_type in component_listener_types:
            wrapper = commands.Cog.listener(listener_type)(wrapper)
        return functools.update_wrapper(wrapper, func)

    return decorator


def component_with_id(
    *, id: t.Optional[str] = None, regex: t.Union[str, re.Pattern, None] = None
) -> t.Callable[[ComponentListenerT], ComponentListenerT]:
    """Create a listener for any kind of component. Specify either `id` or `regex` to which
    the incoming component `custom_id`s are compared.

    Parameters
    ----------
    id: Optional[:class:`str`]
        The custom_id of the component that should be handled.
    regex: Union[:class:`re.Pattern`, :class:`str`, `None`]

    Raises
    ------
    ValueError
        Either `id` or `regex` should be used, not both or neither.
    TypeError
        `id` or `regex` were correctly passed, but of incorrect type.
    """
    return _component_with_id("on_message_interaction", id=id, regex=regex)


def button_with_id(
    *, id: t.Optional[str] = None, regex: t.Union[str, re.Pattern, None] = None
) -> t.Callable[[ComponentListenerT], ComponentListenerT]:
    """Create a listener for a button. Specify either `id` or `regex` to which
    the incoming component `custom_id`s are compared.

    Parameters
    ----------
    id: Optional[:class:`str`]
        The custom_id of the component that should be handled.
    regex: Union[:class:`re.Pattern`, :class:`str`, `None`]

    Raises
    ------
    ValueError
        Either `id` or `regex` should be used, not both or neither.
    TypeError
        `id` or `regex` were correctly passed, but of incorrect type.
    """
    return _component_with_id("on_button_click", id=id, regex=regex)


def dropdown_with_id(
    *, id: t.Optional[str] = None, regex: t.Union[str, re.Pattern, None] = None
) -> t.Callable[[ComponentListenerT], ComponentListenerT]:
    """Create a listener for a select/dropdown. Specify either `id` or `regex` to which
    the incoming component `custom_id`s are compared.

    Parameters
    ----------
    id: Optional[:class:`str`]
        The custom_id of the component that should be handled.
    regex: Union[:class:`re.Pattern`, :class:`str`, `None`]

    Raises
    ------
    ValueError
        Either `id` or `regex` should be used, not both or neither.
    TypeError
        `id` or `regex` were correctly passed, but of incorrect type.
    """
    return _component_with_id("on_dropdown", id=id, regex=regex)


select_with_id = dropdown_with_id
