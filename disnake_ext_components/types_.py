from __future__ import annotations

import enum
import re
import sys
import typing as t

import disnake

__all__ = [
    "Annotated",
    "get_args",
    "get_origin",
    "ListenerType",
    "Converted",
]


_T = t.TypeVar("_T")
_T_co = t.TypeVar("_T_co", covariant=True)
_T_contra = t.TypeVar("_T_contra", contravariant=True)

Coro = t.Coroutine[t.Any, t.Any, _T]
MaybeCoro = t.Union[Coro[_T], _T]
MaybeSequence = t.Union[t.Sequence[_T], _T]

InteractionT = t.TypeVar("InteractionT", disnake.MessageInteraction, disnake.ModalInteraction)
MessageComponentT = t.TypeVar(
    "MessageComponentT",
    bound=t.Union[
        disnake.ui.Button[t.Any],
        disnake.ui.Select[t.Any],
    ],
)

CheckCallback = t.Callable[[InteractionT], MaybeCoro[bool]]
CheckT = t.TypeVar("CheckT", bound=CheckCallback[t.Any])

if sys.version_info >= (3, 10):
    from typing import Annotated, get_args, get_origin
else:
    from typing_extensions import Annotated, get_args, get_origin


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


class ToConverterProtocol(t.Protocol[_T_co]):
    def __call__(self, __argument: str, *args: t.Any) -> _T_co:
        ...


class FromConverterProtocol(t.Protocol[_T_contra]):
    def __call__(self, __argument: _T_contra, *args: t.Any) -> str:
        ...


class _SpecialType(type):
    def __new__(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return super().__new__(cls, cls.__name__, (), {})


class _ConvertedMeta(type):
    def __getitem__(
        self,
        args: t.Tuple[
            t.Union[str, t.Pattern[str]],
            ToConverterProtocol[_T],
            FromConverterProtocol[_T],
        ],
    ) -> t.Type[_T]:
        regex, converter_to, converter_from = args
        if isinstance(regex, str):
            regex = re.compile(re.escape(regex))

        return t.cast(t.Type[_T], Converted(regex, converter_to, converter_from))


class Converted(_SpecialType, metaclass=_ConvertedMeta):
    """Type annotation to denote a custom converter. Provide a regex pattern to match the argument
    with before attempting conversion, a converter function to convert the input from string to
    a given type, and lastly a converter function to convert back to a string.

    Used as a typehint! For example, a converter function parameter could be annotated as follows:
    ```py
    pat = re.Pattern(r".*")

    def to_list(arg: str) -> typing.List[str]:
        return list(str)

    def to_str(arg: typing.List[str]) -> str:
        return "".join(arg)

    @components.component_listener()
    async def listener(
        inter: disnake.MessageInteraction,
        param: Converted[pat, to_list, to_str]
    ):
        ...
    ````
    This would first check if the input matches the provided regex. If it matches, the ``to_str``
    converter is used to convert the input to a list. Use the regex to make sure this is possible!
    Lastly, ``to_str`` is used when auto-generating a `custom_id` to make sure the value can be
    matched again the next time it crosses the listener.
    """

    regex: t.Pattern[str]
    """The regex pattern to which input must conform for the custom converter. To match anything,
    simply provide pattern ".*".
    """

    # TODO: Should probably rename these.

    converter_to: t.Callable[..., MaybeCoro[t.Any]]
    """The custom converter function used to convert input from :class:`str` to the return type
    of the function. Make sure that this function can convert anything matched by the provided
    regex pattern.
    """

    converter_from: t.Callable[..., MaybeCoro[t.Any]]
    """The custom converter function used to convert back to :class:`str`. This is used to ensure
    the value is inserted into the custom_id in such a manner that it can be matched anew. Make
    sure that whatever is returned by this function can be matched by the provided regex pattern.
    """

    def __init__(
        self,
        regex: t.Pattern[str],
        converter_to: t.Callable[..., MaybeCoro[t.Any]],
        converter_from: t.Callable[..., MaybeCoro[t.Any]],
    ):
        self.regex = regex
        self.converter_to = converter_to
        self.converter_from = converter_from

    def __repr__(self):
        return (
            f'Converted[regex=r"{self.regex.pattern}", '
            f"converter_to={self.converter_to.__name__}(), "
            f"converter_from={self.converter_from.__name__}()]"
        )


class SelectOption(disnake.SelectOption):
    __slots__ = ()

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, disnake.SelectOption):
            return False

        for slot in disnake.SelectOption.__slots__:
            value = getattr(self, slot)
            other_value = getattr(other, slot)

            if value is disnake.utils.MISSING and other_value is not disnake.utils.MISSING:
                return False

            if other_value != value:
                return False

        return True

    @classmethod
    def _convert(cls, other: disnake.SelectOption):
        return cls(**{slot: getattr(other, slot) for slot in disnake.SelectOption.__slots__})


def _parse_select_options(
    options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str]]
) -> t.List[SelectOption]:
    # Had to yoink this from disnake as the `ui.select` module is shadowed by the decorator...
    # Gave me the opportunity to work with custom SelectOptions that support comparison though.

    if isinstance(options, dict):
        return [SelectOption(label=key, value=val) for key, val in options.items()]

    return [
        SelectOption._convert(opt)
        if isinstance(opt, disnake.SelectOption)
        else SelectOption(label=opt)
        for opt in options
    ]


class AbstractComponent:
    __sentinel = object()

    __slots__: t.Tuple[t.Any] = tuple(
        set(disnake.Component.__slots__)
        | set(disnake.Button.__slots__)
        | set(disnake.SelectMenu.__slots__)
    )

    def __init__(self, **kwargs: t.Any):
        # Handle special cases...
        if "emoji" in kwargs and isinstance(emoji := kwargs["emoji"], str):
            kwargs["emoji"] = disnake.PartialEmoji.from_str(emoji)

        if "options" in kwargs:
            kwargs["options"] = _parse_select_options(kwargs["options"] or [])

        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_component(
        cls,
        component: t.Union[
            disnake.Button,
            disnake.ui.Button[t.Any],
            disnake.SelectMenu,
            disnake.ui.Select[t.Any],
        ],
    ) -> AbstractComponent:
        self = cls()
        for slot in cls.__slots__:
            value = getattr(component, slot, cls.__sentinel)
            if value is not cls.__sentinel:
                setattr(self, slot, value)

        # Ensure custom SelectOptions
        options: t.Any = getattr(self, "options", self.__sentinel)
        if options is not self.__sentinel:
            setattr(self, "options", _parse_select_options(options))  # noqa: B010

        return self

    def __iter__(self) -> t.Generator[t.Tuple[str, t.Any], None, None]:
        for slot in self.__slots__:
            value = getattr(self, slot, self.__sentinel)
            if value is not self.__sentinel:
                yield slot, value

    def __eq__(self, other: t.Union[disnake.Button, disnake.SelectMenu]) -> bool:  # type: ignore
        return not any(value != getattr(other, slot, self.__sentinel) for slot, value in self)

    def __repr__(self):
        return f"AbstractComponent({', '.join(f'{k}={v}' for k, v in self)})"

    def get(self, key: str) -> t.Optional[t.Any]:
        return getattr(self, key, None)

    def copy(self) -> AbstractComponent:
        return AbstractComponent(**dict(self))

    def with_overrides(self, **kwargs: t.Any):
        copy = self.copy()
        copy.__init__(**{k: v for k, v in kwargs.items() if v is not None})
        return copy

    def as_component(self, template: t.Type[MessageComponentT]) -> MessageComponentT:
        kwargs = dict(self)
        type_ = kwargs.pop("type", self.__sentinel)

        component = template(**kwargs)
        if component.type is not type_:
            raise ValueError(
                f"This AbstractComponent is of type {type_}, "
                f"and is therefore incompatible with {template.__name__}."
            )

        return component
