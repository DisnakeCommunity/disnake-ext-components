from __future__ import annotations

import inspect
import re
import sys
import typing as t

import disnake
from disnake.ext import commands

from . import params, types_

__all__ = ["component_listener", "ComponentListener"]


if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec

else:
    from typing_extensions import Concatenate, ParamSpec

AwaitableT = t.TypeVar("AwaitableT", bound=t.Awaitable[t.Any])
T = t.TypeVar("T")
P = ParamSpec("P")

ListenerT = t.TypeVar("ListenerT", bound="ComponentListener[t.Any, t.Any]")

CogT = t.TypeVar("CogT", bound=commands.Cog)
ListenerSpec = Concatenate[CogT, disnake.MessageInteraction, P]


def id_spec_from_signature(name: str, sep: str, signature: inspect.Signature) -> str:
    """Analyze a function signature to create a format string for creating new custom_ids.

    Parameters
    ----------
    name: :class:`str`
        The name of the listener function to which the signature belongs.
    signature: :class:`inspect.Signature`
        The function signature of the listener function.
    """
    return (
        name + sep + sep.join(f"{{{param.name}}}" for param in extract_listener_params(signature))
    )


def id_spec_from_regex(regex: t.Pattern[str]) -> str:
    """Analyze a regex pattern for a component custom_id to create a format string for creating
    new custom_ids.

    Parameters
    ----------
    regex: :class:`re.Pattern`
        The regex pattern that is to be deconstructed.
    """
    return re.sub(r"\(\?P<(.+?)>.*?\)", lambda m: f"{{{m[1]}}}", regex.pattern)


class ComponentListener(types_.partial[t.Awaitable[T]], t.Generic[P, T]):
    """An advanced component listener that supports syntax similar to disnake slash commands.

    Features:
    - Automated `custom_id` matching through regex,
    - Automated type-conversion similar to slash commands,
    - Helper methods to build new components with valid `custom_id`s,
    - Error handling.  (soon:tm:)

    Mainly created using :func:`~component_listener`.

    Parameters
    ----------
    func: :class:`types.ComponentListenerFunc`
        The function that is to be turned into a decorator. Will honor the full signature of the
        function: any parameters are used to store/parse state to/from `custom_id`s, and any
        annotations are used to convert incoming `custom_id` :class:`str`s to the desired type.
        As of right now, this only supports :class:`commands.Cog` listeners.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        If provided, this will override the default behavior of automatically generating matching
        regex for the listener, and will use custom regex instead. For the listener to fire, the
        incoming `custom_id` must pass being `re.fullmatch`ed with this regex.
    sep: :class:`str`
        The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
        Under normal circumstances, this should not lead to conflicts. In case ':' is intentionally
        part of the `custom_id`s matched by the listener, this should be set to a different value
        to prevent conflicts.
    """

    # These are just to conform to dpy listener spec
    __name__: str
    __cog_listener__: t.Final[t.Literal[True]] = True
    __cog_listener_names__: t.List[str] = [types_.ListenerType.MESSAGE_INTERACTION]

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

    param_names: t.List[str]
    """A list of names of the processed listener function parameters."""

    def __new__(
        cls: t.Type[ListenerT],
        func: t.Callable[ListenerSpec[t.Any, P], t.Awaitable[T]],
        **kwargs: t.Any,
    ) -> ListenerT:
        self = super().__new__(cls, func)
        self.__name__ = func.__name__
        return self

    def __init__(
        self,
        func: t.Callable[ListenerSpec[t.Any, P], t.Awaitable[T]],
        *,
        type: types_.ListenerType = types_.ListenerType.MESSAGE_INTERACTION,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
    ) -> None:
        self.__cog_listener_names__ = [type]
        self._signature = commands.params.signature(func)  # pyright: ignore
        if regex:
            self.regex = ensure_compiled(regex)
            self.id_spec = id_spec_from_regex(self.regex)
            self.sep = None
        else:
            self.regex = None
            self.id_spec = id_spec_from_signature(self.__name__, sep, self._signature)
            self.sep = sep

        listener_params = extract_listener_params(self._signature)
        self.params = [params.ParamInfo.from_param(param) for param in listener_params]
        self.param_names = [paraminfo.param.name for paraminfo in self.params]

    def __get__(self: ListenerT, instance: t.Any, _) -> ListenerT:
        """Abuse descriptor functionality to inject instance of the owner class as first arg."""
        # Inject instance of the owner class as the partial's first arg.
        # If need be, we could add support for classmethods by checking the
        # type of self.func and injecting the owner class instead where appropriate.
        self.__setstate__((self.func, (instance,), {}, self.__dict__))  # type: ignore
        return self

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.MessageInteraction,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:  # Has to be able to short-circuit, so we'll have to accept mistyping this.
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
        if args:
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
            args_as_kwargs = dict(zip(self.param_names, args))

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

    def error(self) -> t.NoReturn:
        """Register an error handler for this listener.
        Note: Not yet implemented.
        """
        raise NotImplementedError()


def component_listener(
    *,
    type: types_.ListenerType = types_.ListenerType.MESSAGE_INTERACTION,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[t.Callable[ListenerSpec[CogT, P], AwaitableT]], ComponentListener[P, AwaitableT]]:
    """Create a new :class:`ComponentListener` from a decorated function. This function must
    contain a parameter annotated as :class:`disnake.MessageInteraction`. By default, this will
    create a component listener that can handle stateful `custom_id`s and aid in their creation.

    Parameters
    ----------
    type: :class:`types.ListenerType`
        The type of interactions this listener should respond to. By default, the listener uses
        event `message_interaction`, which means it responds to both buttons and selects.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`ComponentListener` use the default parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.
    """

    def wrapper(
        func: t.Callable[ListenerSpec[CogT, P], AwaitableT],
    ) -> ComponentListener[P, AwaitableT]:
        listener = ComponentListener(func, type=type, regex=regex, sep=sep)

        if bot is not None:
            bot.add_listener(listener, type)

        return listener

    return wrapper


def extract_listener_params(signature: inspect.Signature) -> t.Iterator[inspect.Parameter]:
    """Extract the parameters of the listener function that are used to analyze incoming
    custom_ids. This function strips `self` if the listener is in a Cog, and the
    :class:`disnake.MessageInteraction` parameter.

    Parameters
    ----------
    signature: :class:`inspect.Signature`
        The (full) function signature of the listener function.

    Raises
    ------
    TypeError:
        The function signature did not contain any parameters annotated as
        :class:`disnake.MessageInteraction`. This is required to properly split the signature.

    Returns
    -------
    Iterator[:class:`inspect.Parameter`]:
        An iterator of the parameters used to analyze incoming custom_ids. This includes all
        parameters on the listener except `self` and the `disnake.MessageInteraction` parameter.
    """
    param_iter = iter(signature.parameters.values())
    for param in param_iter:
        if param.annotation is disnake.MessageInteraction:
            break
    else:
        raise TypeError(
            "No interaction parameter (annotated as 'disnake.MessageInteraction') was found.\n"
            "Please make sure the interaction parameter is properly annotated in the listener."
        )
    return param_iter


def ensure_compiled(
    pattern: t.Union[str, t.Pattern[str]],
    flags: re.RegexFlag = re.UNICODE,  # seems to be the default of re.compile
) -> t.Pattern[str]:
    """Ensure a regex pattern is compiled.

    Parameters
    ----------
    pattern: Union[:class:`str`, :class:`re.Pattern`]
        The pattern that should be force-compiled into a :class:`re.Pattern`. If this already is
        compiled, it is returned as-is.
    flags: :class:`re.RegexFlag`
        Any flags to apply to compilation. By default this has the same behaviour as `re.compile`.
    """
    return re.compile(pattern, flags) if isinstance(pattern, str) else pattern
