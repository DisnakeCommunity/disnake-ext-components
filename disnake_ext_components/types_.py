import enum
import typing as t

__all__ = ["ListenerType"]

# class ComponentListenerFunc(t.Protocol):
#     #__name__: t.Optional[str]

#     def __call__(_, self: t.Any, inter: t.Any, *args: t.Any) -> t.Coroutine[t.Any, t.Any, t.Any]:
#         ...


class ListenerType(str, enum.Enum):
    """A string enum that contains all listener types."""

    BUTTON = "on_button_click"
    """Listener event for button presses."""

    SELECT = DROPDOWN = "on_select"
    """Listener event for select menus."""

    MESSAGE_INTERACTION = ANY = ALL = "on_message_interaction"
    """Listener event for any component."""
