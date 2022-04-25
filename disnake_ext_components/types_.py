from __future__ import annotations

import enum
import functools
import re
import sys
import typing as t

__all__ = [
    "Annotated",
    "get_args",
    "get_origin",
    "ListenerType",
    "partial",
    "Converted",
    "SelectValue",
]


_T = t.TypeVar("_T")

MaybeAwaitable = t.Union[t.Awaitable[_T], _T]
MaybeSequence = t.Union[t.Sequence[_T], _T]


if sys.version_info >= (3, 10):
    from typing import Annotated, get_args, get_origin
else:
    from typing_extensions import Annotated, get_args, get_origin

if sys.version_info >= (3, 9):
    partial = functools.partial

else:

    class partial(functools.partial, t.Generic[_T]):  # pyright: ignore
        """This intermediary class is needed to have type-checking work properly between Python
        versions 3.8 through 3.10. Since `functools.partial` became a generic in Python 3.9,
        type-checkers expect this in versions 3.9 and up, whereas it would raise in version 3.8.

        To get around this, for version 3.8 specifically, we create this intermediary class to
        make `functools.partial` behave like its version 3.9+ counterpart, where the return type
        can be set as the generic type specifier.
        """

        def __call__(self, *args: t.Any, **kwargs: t.Any) -> _T:
            return t.cast(_T, super().__call__(*args, **kwargs))


class ListenerType(str, enum.Enum):
    """A string enum that contains all listener types."""

    BUTTON = "on_button_click"
    """Listener event for button presses."""

    SELECT = DROPDOWN = "on_dropdown"
    """Listener event for select menus."""

    MESSAGE_INTERACTION = COMPONENT = "on_message_interaction"
    """Listener event for any component."""

    MODAL = "on_modal_submit"
    """Listener event for modals."""


class _SpecialType(type):
    def __new__(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return super().__new__(cls, cls.__name__, (), {})


class _ConvertedMeta(type):
    def __getitem__(
        self,
        args: t.Tuple[
            t.Union[str, t.Pattern[str]],
            MaybeSequence[t.Callable[..., MaybeAwaitable[_T]]],
        ],
    ) -> t.Type[_T]:
        regex, converters = args
        if isinstance(regex, str):
            regex = re.compile(re.escape(regex))

        if not isinstance(converters, t.Sequence):
            converters = (converters,)

        return t.cast(t.Type[_T], Converted(regex, *converters))


class Converted(_SpecialType, metaclass=_ConvertedMeta):
    """Type annotation to denote a custom converter. Provide a regex pattern to match the argument
    with before attempting conversion, and a (sequence of) converter function(s) with which to
    transform the argument.

    Used as a typehint! For example, a converter function parameter could be annotated as follows:
    ```py
    @components.component_listener()
    async def listener(
        inter: disnake.MessageInteraction,
        param: Converted[r"/d+\\.?\\d*", [float, round]]
    ):
        ...
    ````
    This would first check if the input matches the provided regex to see if it can be a float.
    Next, it would actually convert the input to a float, and lastly, it would round the float.
    """

    regex: t.Pattern[str]
    """The regex pattern to which input must conform for the custom converter. To match anything,
    simply provide pattern ".*".
    """

    converters: t.Tuple[t.Callable[..., MaybeAwaitable[t.Any]]]
    """The custom converter functions. Must take at least a string, which is the argument that is to
    be converted. This function may also take the interaction: `inter: disnake.MessageInteraction`
    or `inter: disnake.ModalInteraction` depending on the listener type. Finally, it may also take
    `converted: List[Any]`, which contains all the previously converted values.
    """

    def __init__(self, regex: t.Pattern[str], *converters: t.Callable[..., MaybeAwaitable[t.Any]]):
        self.regex = regex
        self.converters = converters

    def __repr__(self):
        converters = f"({', '.join(converter.__name__ for converter in self.converters)})"
        return f'Converted[regex=r"{self.regex.pattern}", converters={converters}]'


class SpecialValues(enum.Enum):
    SELECT = enum.auto()
    MODAL = enum.auto()


SelectValue = Annotated[_T, SpecialValues.SELECT]

ModalValue = Annotated[_T, SpecialValues.MODAL]  # not sure about this one yet...
