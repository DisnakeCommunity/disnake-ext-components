from __future__ import annotations

import abc
import sys
import typing as t

import disnake
from disnake.ext import commands

from . import params, types_, utils

__all__ = [
    "button_listener",
    "ButtonListener",
    "select_listener",
    "SelectListener",
]


if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec

else:
    from typing_extensions import Concatenate, ParamSpec

T = t.TypeVar("T")  # listener return type
VT = t.TypeVar("VT")  # type of select value
P = ParamSpec("P")

MaybeCollection = t.Union[t.Collection[T], T]
CogT = t.TypeVar("CogT", bound=commands.Cog)
ListenerT = t.TypeVar("ListenerT", bound="_BaseListener[t.Any, t.Any, t.Any]")

InteractionT = t.TypeVar("InteractionT", disnake.MessageInteraction, disnake.ModalInteraction)
ErrorHandlerT = t.Callable[[CogT, InteractionT, Exception], t.Any]

ButtonListenerSpec = Concatenate[CogT, disnake.MessageInteraction, P]
SelectListenerSpec = Concatenate[CogT, disnake.MessageInteraction, types_.SelectValue[VT], P]
# ModalListenerSpec = t.Union[
#     Concatenate[CogT, InteractionT, types_.ModalValue[t.Any], P],
#     Concatenate[CogT, InteractionT, types_.ModalValue[t.Any], types_.ModalValue[t.Any], P]
# ]


class _BaseListener(types_.partial[t.Awaitable[T]], abc.ABC, t.Generic[P, T, InteractionT]):

    # These are just to conform to dpy listener spec
    __name__: str
    __cog_listener__: t.Final[t.Literal[True]] = True
    __cog_listener_names__: t.List[types_.ListenerType]

    id_spec: str
    """The spec that inbound `custom_id`s should match. Also used to create new custom ids; see
    `~.build_custom_id`.
    """

    regex: t.Optional[t.Pattern[str]]
    """The user-defined regex pattern against which incoming `custom_id`s are matched.
    `None` if the user did not define custom regex, in which case parsing is done automatically.
    """

    sep: t.Optional[str]
    """The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
    Only applicable if custom regex has not been set. If it has, this will be `None` instead.
    """

    params: t.List[params.ParamInfo]
    """A list that contains processed listener function parameters with `self` and the
    `disnake.MessageInteraction` parameter stripped off. These parameters contain extra information
    about their regex pattern(s) and converter(s).
    """

    def __new__(
        cls: t.Type[ListenerT],
        func: t.Callable[..., t.Awaitable[T]],
        **kwargs: t.Any,
    ) -> ListenerT:
        self = super().__new__(cls, func)
        self.__name__ = func.__name__
        return self

    def __get__(self: ListenerT, instance: t.Any, _) -> ListenerT:
        """Abuse descriptor functionality to inject instance of the owner class as first arg."""
        # Inject instance of the owner class as the partial's first arg.
        # If need be, we could add support for classmethods by checking the
        # type of self.func and injecting the owner class instead where appropriate.
        self.__setstate__((self.func, (instance,), {}, self.__dict__))  # type: ignore
        return self

    def error(
        self, func: t.Callable[[CogT, InteractionT, Exception], t.Any]
    ) -> t.Callable[[CogT, InteractionT, Exception], t.Any]:
        """Register an error handler for this listener.
        Note: Not yet implemented.
        """
        raise NotImplementedError()

    def parse_custom_id(self, custom_id: str) -> t.Tuple[str, ...]:
        """Parse an incoming custom_id into its name and raw parameter values.

        Parameters
        ----------
        custom_id: :class:`str`
            The custom_id that is to be parsed.

        Raises
        ------
        ValueError:
            The custom_id is not valid for this listener.

        Returns
        -------
        Tuple[:class:`str`, ...]:
            The raw parameter values extracted from the custom_id.
        """
        if self.regex:
            match = self.regex.fullmatch(custom_id)
            if not match or len(params := match.groupdict()) != len(self.params):
                raise ValueError(f"Regex pattern {self.regex} did not match custom_id {custom_id}.")

            return tuple(params.values())

        name, *params = custom_id.split(self.sep)
        if name != self.__name__ or len(params) != len(self.params):
            raise ValueError(f"Listener spec {self.id_spec} did not match custom_id {custom_id}.")

        return tuple(params)

    def build_custom_id(self, *args: P.args, **kwargs: P.kwargs) -> str:
        """Build a custom_id by passing values for the listener's parameters. This way, assuming
        the values entered are valid according to the listener's typehints, the custom_id is
        guaranteed to be matched by the listener.

        Note: No actual validation is done on the values entered.

        Parameters
        ----------
        *args: :class:`Any`
            This method takes the same arguments as the decorated listener function itself, and
            will be used to build a `custom_id` conform to the spec of the listener.
        **kwargs: :class:`Any`
            Any of the args as mentioned above can also be passed as keyword arguments.

        Returns
        -------
        :class:`str`
            A custom_id matching the spec of this listener.
        """
        if args:
            # Change args into kwargs such that they're accepted by str.format
            args_as_kwargs = dict(zip([param.name for param in self.params], args))

            if overlap := kwargs.keys() & args_as_kwargs:
                # Emulate standard python behaviour by disallowing duplicate names for args/kwargs.
                first = next(iter(overlap))
                raise TypeError(f"'build_custom_id' got multiple values for argument '{first}'")

            kwargs.update(args_as_kwargs)  # This is safe as we ensured there is no overlap.

        # "Deserialize" discord types with id to their id (int)
        kwargs = {k: getattr(v, "id", v) for k, v in kwargs.items()}  # pyright: ignore

        if self.regex:
            return self.id_spec.format(**kwargs)
        return self.id_spec.format(sep=self.sep, **kwargs)


class ButtonListener(_BaseListener[P, T, disnake.MessageInteraction]):
    """An advanced component listener that supports syntax similar to disnake slash commands.

    Features:
    - Automated `custom_id` matching through regex,
    - Automated type-conversion similar to slash commands,
    - Helper methods to build new components with valid `custom_id`s,
    - Error handling.  (soon:tm:)

    Mainly created using :func:`components.button_listener`.

    Parameters
    ----------
    func: Callable[[...], Any]
        The function that is to be used as callback for the listener. A :class:`ButtonListener`
        requires the first (non-self) parameter to be annotated as `disnake.MessageInteraction`.
        If the listener is invoked because a matching component is interacted with, the input is
        converted to match the function's annotations.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        If provided, this will override the default behavior of automatically generating matching
        regex for the listener, and will use custom regex instead. For the listener to fire, the
        incoming `custom_id` must pass being `re.fullmatch`ed with this regex. Use named capture
        groups to match group names with function parameter names.
    sep: :class:`str`
        The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
        Under normal circumstances, this should not lead to conflicts. In case ':' is intentionally
        part of the `custom_id`s matched by the listener, this should be set to a different value
        to prevent conflicts.
    """

    __cog_listener_names__: t.List[types_.ListenerType] = [types_.ListenerType.BUTTON]

    def __new__(
        cls: t.Type[ListenerT],
        func: t.Callable[ButtonListenerSpec[CogT, P], t.Awaitable[T]],
        **kwargs: t.Any,
    ) -> ListenerT:
        return super().__new__(cls, func, **kwargs)

    def __init__(
        self,
        func: t.Callable[ButtonListenerSpec[CogT, P], t.Awaitable[T]],
        *,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
    ) -> None:
        self._signature = commands.params.signature(func)  # pyright: ignore
        if regex:
            self.regex = utils.ensure_compiled(regex)
            self.id_spec = utils.id_spec_from_regex(self.regex)
            self.sep = None
        else:
            self.regex = None
            self.id_spec = utils.id_spec_from_signature(self.__name__, sep, self._signature)
            self.sep = sep

        _, listener_params = utils.extract_listener_params(self._signature)
        self.params = [params.ParamInfo.from_param(param) for param in listener_params]

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.MessageInteraction,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:
        """Run all parameter converters, and if everything correctly converted, run the listener
        callback with the converted arguments.

        Parameters
        ----------
        inter: :class:`disnake.MessageInteraction`
            The interaction that intiated the listener.
        *args: Any
            Any arguments passed to the listener. Only really relevant when the listener is
            called manually. In all other cases, args will be empty, and parsing will instead
            be done based on the custom_id of the interaction.
            Note that arguments passed manually will be assumed correct, and will not be converted.

        Returns
        -------
        Any:
            If the decorated listener function is made to return anything, it will similarly
            be returned here. In all other cases, this will return `None`.
        """
        if args or kwargs:
            # The user manually called the listener so we skip any checks and just run.
            # Inter may thus not actually be an inter, but I feel like that's on the user.
            x = super().__call__(inter, *args, **kwargs)
            return await x

        if (custom_id := inter.component.custom_id) is None:
            return

        try:
            custom_id_params = self.parse_custom_id(custom_id)
        except ValueError:
            return

        converted: t.List[t.Any] = []
        for param, arg in zip(self.params, custom_id_params):
            converted.append(
                await param.convert(
                    arg,
                    inter=inter,
                    converted=converted,
                    skip_validation=bool(self.regex),
                )
            )

        return await super().__call__(inter, *converted)


def button_listener(
    *,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[t.Callable[ButtonListenerSpec[CogT, P], t.Awaitable[T]]], ButtonListener[P, T]]:
    """Create a new :class:`ButtonListener` from a decorated function. The :class:`ButtonListener`
    will take care of regex-matching and persistent data stored in the `custom_id` of the
    :class:`disnake.ui.Button`.

    - The first parameter of the function (disregarding `self` inside a cog) is the
    :class:`disnake.MessageInteraction`.
    - Any remaining parameters are stored in and resolved from the `custom_id`.

    Parameters
    ----------
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`ButtonListener` use the default automatic parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.

    Returns
    -------
    :class:`ButtonListener`
        The newly created :class:`ButtonListener`.
    """

    def wrapper(
        func: t.Callable[ButtonListenerSpec[CogT, P], t.Awaitable[T]],
    ) -> ButtonListener[P, T]:
        listener = ButtonListener(func, regex=regex, sep=sep)

        if bot is not None:
            bot.add_listener(listener, types_.ListenerType.BUTTON)

        return listener

    return wrapper


class SelectListener(_BaseListener[P, T, disnake.MessageInteraction], t.Generic[P, VT, T]):
    """An advanced component listener that supports syntax similar to disnake slash commands.

    Features:
    - Automated `custom_id` matching through regex,
    - Automated type-conversion similar to slash commands,
    - Helper methods to build new components with valid `custom_id`s,
    - Error handling.  (soon:tm:)

    Mainly created using :func:`components.select_listener`.

    Parameters
    ----------
    func: Callable[[...], Any]
        The function that is to be used as callback for the listener. A :class:`SelectListener`
        requires the first (non-self) parameter to be annotated as `disnake.MessageInteraction`,
        and the second as `components.SelectValue`. If the listener is invoked because a matching
        component is interacted with, the input is converted to match the function's annotations.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        If provided, this will override the default behavior of automatically generating matching
        regex for the listener, and will use custom regex instead. For the listener to fire, the
        incoming `custom_id` must pass being `re.fullmatch`ed with this regex. Use named capture
        groups to match group names with function parameter names.
    sep: :class:`str`
        The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
        Under normal circumstances, this should not lead to conflicts. In case ':' is intentionally
        part of the `custom_id`s matched by the listener, this should be set to a different value
        to prevent conflicts.
    """

    __cog_listener_names__: t.List[types_.ListenerType] = [types_.ListenerType.SELECT]

    def __new__(
        cls: t.Type[ListenerT],
        func: t.Callable[SelectListenerSpec[CogT, MaybeCollection[VT], P], t.Awaitable[T]],
        **kwargs: t.Any,
    ) -> ListenerT:
        return super().__new__(cls, func, **kwargs)

    def __init__(
        self,
        func: t.Callable[SelectListenerSpec[CogT, MaybeCollection[VT], P], t.Awaitable[T]],
        *,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
    ) -> None:
        self._signature = commands.params.signature(func)  # pyright: ignore
        if regex:
            self.regex = utils.ensure_compiled(regex)
            self.id_spec = utils.id_spec_from_regex(self.regex)
            self.sep = None
        else:
            self.regex = None
            self.id_spec = utils.id_spec_from_signature(self.__name__, sep, self._signature)
            self.sep = sep

        special_params, listener_params = utils.extract_listener_params(self._signature)
        self.params = [params.ParamInfo.from_param(param) for param in listener_params]

        if len(special_params) != 1:
            raise TypeError(
                f"A `{type(self).__name__}` must have exactly one parameter annotated as `SelectValue`."
            )
        self.select_param = params.ParamInfo.from_param(special_params[0])

    def _cast_to_return_type(self, values: t.List[VT]) -> t.Union[t.Collection[VT], VT]:
        """Cast a value to the desired return type: either converts the collection to the annotation
        type, or unpacks the value if it is annotated as a non-collection type.
        """
        return_type = types_.get_origin(self.select_param.param.annotation)

        if not issubclass(return_type, t.Collection) or issubclass(return_type, (str, bytes)):
            if len(values) > 1:
                type_name = getattr(return_type, "__name__", repr(return_type))
                raise TypeError(
                    f"Cannot cast multiple values to type `{type_name}`. "
                    f"Consider annotating the parameter as `typing.List[{type_name}]."
                )
            return values[0]

        try:
            return return_type(values)  # pyright: ignore
        except Exception as exc:
            type_name = getattr(return_type, "__name__", repr(return_type))
            raise TypeError(f"Failed to cast list of select values to type {type_name!r}.") from exc

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.MessageInteraction,
        select_value: VT = disnake.utils.MISSING,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:
        """Run all parameter converters, and if everything correctly converted, run the listener
        callback with the converted arguments.

        Parameters
        ----------
        inter: :class:`disnake.MessageInteraction`
            The interaction that intiated the listener.
        *args: Any
            Any arguments passed to the listener. Only really relevant when the listener is
            called manually. In all other cases, args will be empty, and parsing will instead
            be done based on the custom_id of the interaction.
            Note that arguments passed manually will be assumed correct, and will not be converted.

        Returns
        -------
        Any:
            If the decorated listener function is made to return anything, it will similarly
            be returned here. In all other cases, this will return `None`.
        """
        if args or kwargs:
            # The user manually called the listener so we skip any checks and just run.
            # Inter may thus not actually be an inter, but I feel like that's on the user.
            x = super().__call__(inter, select_value, *args, **kwargs)
            return await x

        if not inter.values or (custom_id := inter.component.custom_id) is None:
            return

        try:
            custom_id_params = self.parse_custom_id(custom_id)
        except ValueError:
            return

        # First convert custom_id params...
        converted: t.List[t.Any] = []
        for param, arg in zip(self.params, custom_id_params):
            converted.append(
                await param.convert(
                    arg,
                    inter=inter,
                    converted=converted,
                    skip_validation=bool(self.regex),
                )
            )

        converted_values = await self.select_param.convert(
            inter.values, inter=inter, converted=converted
        )

        return await super().__call__(
            inter, self._cast_to_return_type(converted_values), *converted
        )


def select_listener(
    *,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[
    [t.Callable[SelectListenerSpec[CogT, VT, P], t.Awaitable[T]]],
    SelectListener[P, VT, T],
]:
    """Create a new :class:`SelectListener` from a decorated function. The :class:`SelectListener`
    will take care of regex-matching and persistent data stored in the `custom_id` of the
    :class:`disnake.ui.Select`.

    - The first parameter of the function (disregarding `self` inside a cog) is the
    :class:`disnake.MessageInteraction`.
    - The next parameter will receive the selected values, and should be annotated as
    :class:`.SelectValue`. This should be narrowed down with an inner type. In case e.g. a list of
    strings is desired for all the values, the annotation would be
    `param: components.SelectValue[typing.List[str]]`.
    - Any remaining parameters are stored in and resolved from the `custom_id`.

    Parameters
    ----------
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`SelectListener` use the default automatic parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.

    Returns
    -------
    :class:`SelectListener`
        The newly created :class:`SelectListener`.
    """

    def wrapper(
        func: t.Callable[SelectListenerSpec[CogT, VT, P], t.Awaitable[T]],
    ) -> SelectListener[P, VT, T]:
        listener = SelectListener[P, VT, T](func, regex=regex, sep=sep)

        if bot is not None:
            bot.add_listener(listener, types_.ListenerType.SELECT)

        return listener

    return wrapper
