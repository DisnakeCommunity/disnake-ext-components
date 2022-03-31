import enum

__all__ = ["ListenerType"]


class ListenerType(str, enum.Enum):
    """A string enum that contains all listener types."""

    BUTTON = "on_button_click"
    """Listener event for button presses."""

    SELECT = DROPDOWN = "on_select"
    """Listener event for select menus."""

    MESSAGE_INTERACTION = ANY = ALL = "on_message_interaction"
    """Listener event for any component."""
