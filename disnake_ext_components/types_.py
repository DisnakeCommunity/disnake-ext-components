from __future__ import annotations

import enum
import functools
import sys
import typing as t

__all__ = ["ListenerType", "partial"]


_T = t.TypeVar("_T")


class ListenerType(str, enum.Enum):
    """A string enum that contains all listener types."""

    BUTTON = "on_button_click"
    """Listener event for button presses."""

    SELECT = DROPDOWN = "on_select"
    """Listener event for select menus."""

    MESSAGE_INTERACTION = ANY = ALL = "on_message_interaction"
    """Listener event for any component."""


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
