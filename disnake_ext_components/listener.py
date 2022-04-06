from __future__ import annotations

import functools
import inspect
import re
import typing as t

import disnake
from disnake.ext import commands
from disnake.ext.commands import params as cmd_params

from . import params, types_

__all__ = ["component_listener", "ComponentListener"]


ComponentListenerFunc = t.Callable[..., t.Awaitable[t.Any]]
ListenerT = t.TypeVar("ListenerT", bound="ComponentListener")


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


def id_spec_from_regex(regex: re.Pattern) -> str:
    """Analyze a regex pattern for a component custom_id to create a format string for creating
    new custom_ids.

    Parameters
    ----------
    regex: :class:`re.Pattern`
        The regex pattern that is to be deconstructed.
    """
    return re.sub(r"\(\?P<(.+?)>.*?\)", lambda m: f"{{{m[1]}}}", regex.pattern)


class ComponentListener(functools.partial):
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

    regex: t.Optional[re.Pattern]
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

    def __new__(cls: t.Type[ListenerT], func: t.Callable[..., t.Any], **kwargs: t.Any) -> ListenerT:
        self = super().__new__(cls, func)
        self.__name__ = func.__name__
        return self

    def __init__(
        self,
        func: ComponentListenerFunc,
        *,
        type: types_.ListenerType = types_.ListenerType.MESSAGE_INTERACTION,
        regex: t.Union[str, re.Pattern, None] = None,
        sep: str = ":",
    ) -> None:
        self.__cog_listener_names__ = [type]
        self._signature = cmd_params.signature(func)
        if regex:
            self.regex = ensure_compiled(regex)
            self.id_spec = id_spec_from_regex(self.regex)
            self.sep = None
        else:
            self.regex = None
            self.id_spec = id_spec_from_signature(self.__name__, sep, self._signature)
            self.sep = sep

        self.params = [
            params.ParamInfo.from_param(param) for param in extract_listener_params(self._signature)
        ]

    def __get__(self: ListenerT, instance: t.Any, _) -> ListenerT:
        """Abuse descriptor functionality to inject instance of the owner class as first arg."""
        # Inject instance of the owner class as the partial's first arg.
        # If need be, we could add support for classmethods by checking the
        # type of self.func and injecting the owner class instead where appropriate.
        self.__setstate__((self.func, (instance,), {}, self.__dict__))  # type: ignore
        return self

    async def __call__(self, inter: disnake.MessageInteraction, *args: t.Any) -> t.Any:  # type: ignore
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

        if (custom_id := inter.component.custom_id) is None:
            return

        # Predefined here because super() fails to infer the correct arguments inside a wrapper
        _call = super().__call__
        in_name, *in_params = custom_id.split(self.sep)

        if args:
            # The user manually called the listener so we skip any checks and just run.
            # Inter may thus not actually be an inter, but I feel like that's on the user.
            return await _call(inter, *args)

        elif self.regex:
            # The user entered custom regex, we fullmatch the whole custom_id, then convert
            # individual parameters. For now we still enforce named groups, but this may change.
            if not (_match := self.regex.fullmatch(custom_id)):
                return

            match = _match  # Helps the wrapper understand that this cannot be None.

            async def wrapper() -> t.Any:
                converted = [
                    await param.convert(arg, inter=inter, skip_validation=True)
                    for param, arg in zip(self.params, match.groupdict().values())
                ]
                return await _call(inter, *converted)

        else:
            # We use the 'fully-automatic' spec where we just try to match each parameter
            # separately and then try to convert it. Further control is currently entirely
            # out of the hands of the user, but that could later be added through options.
            if in_name != self.__name__:
                return  # Names don't match, so we can immediately stop parsing.

            async def wrapper() -> t.Any:
                converted = [
                    await param.convert(arg, inter=inter)
                    for param, arg in zip(self.params, in_params)
                ]
                return await _call(inter, *converted)

        return await wrapper()

    def build_custom_id(self, *args: t.Any, **kwargs: t.Any) -> str:
        """Build a custom_id by passing values for the listener's parameters. This way, assuming
        the values entered are valid according to the listener's typehints, the custom_id is
        guaranteed to be matched by the listener.

        Note: No actual validation is done on the values entered.

        Parameters
        -----------
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

        # TODO: deserialize non-int/str/float/bool into str (e.g. Guild -> str(Guild.id))
        if args:
            # Change args into kwargs such that they're accepted by str.format
            args_as_kwargs = {
                paraminfo.param.name: arg for paraminfo, arg in zip(self.params, args)
            }

            if overlap := kwargs.keys() & args_as_kwargs:
                # Emulate standard python behaviour by disallowing duplicate names for args/kwargs
                first = next(iter(overlap))
                raise TypeError(f"'build_custom_id' got multiple values for argument '{first}'")

            kwargs.update(args_as_kwargs)

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
    regex: t.Union[str, re.Pattern, None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[ComponentListenerFunc], ComponentListener]:
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
        func: ComponentListenerFunc,
    ) -> ComponentListener:
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
    pattern: t.Union[str, re.Pattern],
    flags: re.RegexFlag = re.UNICODE,  # seems to be the default of re.compile
) -> re.Pattern:
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
