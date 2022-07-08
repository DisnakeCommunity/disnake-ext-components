import abc
import asyncio.coroutines
import sys
import typing as t

import disnake
from disnake.ext import commands

from . import params, types_, utils

if sys.version_info >= (3, 10):
    from typing import ParamSpec

else:
    from typing_extensions import ParamSpec


T = t.TypeVar("T")
ParentT = t.TypeVar("ParentT")
P = ParamSpec("P")
InteractionT = t.TypeVar("InteractionT", bound=disnake.Interaction)

ListenerT = t.TypeVar("ListenerT", bound="BaseListener[t.Any, t.Any, t.Any]")


class BaseListener(abc.ABC, t.Generic[P, T, InteractionT]):

    # Make asyncio.iscoroutinefunction believe this is a coroutine function...
    _is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore

    # These are just to conform to dpy listener spec...
    __cog_listener__: t.Final[t.Literal[True]] = True
    __cog_listener_names__: t.List[types_.ListenerType]

    parent: t.Optional[t.Any]
    """The class on which this listener is defined, if any.
    Used to set the `self` parameter on the listener.
    """

    callback: t.Callable[..., types_.Coro[T]]
    """The callback function wrapped by this listener."""

    name: str
    """The name of the callback function wrapped by this listener. Used to determine the custom
    id spec for the listener. This can be customized in `~.__init__`.
    """

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

    def __init__(
        self,
        callback: t.Callable[..., types_.Coro[T]],
        *,
        name: t.Optional[str] = None,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
    ) -> None:
        self.parent = None

        self.callback = callback
        self.name = name or callback.__name__
        self._signature = commands.params.signature(callback)  # type: ignore

        if regex:
            self.regex = utils.ensure_compiled(regex)
            self.id_spec = utils.id_spec_from_regex(self.regex)
            self.sep = None

        else:
            self.regex = None
            self.id_spec = utils.id_spec_from_signature(self.__name__, sep, self._signature)
            self.sep = sep

    @property
    def __name__(self):
        return self.name

    def __get__(self: ListenerT, instance: t.Optional[t.Any], _) -> ListenerT:
        """Abuse descriptor functionality to inject instance of the owner class as first arg."""
        # Inject instance of the owner class as the partial's first arg.
        # If need be, we could add support for classmethods by checking the
        # type of self.func and injecting the owner class instead where appropriate.
        self.parent = instance
        return self

    async def __call__(self, *args: t.Any, **kwargs: t.Any) -> T:
        if self.parent:
            return await self.callback(self.parent, *args, **kwargs)
        return await self.callback(*args, **kwargs)

    def error(
        self, func: t.Callable[[ParentT, InteractionT, Exception], t.Any]
    ) -> t.Callable[[ParentT, InteractionT, Exception], t.Any]:
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

    async def build_custom_id(self, *args: P.args, **kwargs: P.kwargs) -> str:
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
            args_as_kwargs: t.Dict[str, t.Any] = dict(
                zip([param.name for param in self.params], args)
            )

            if overlap := kwargs.keys() & args_as_kwargs:
                # Emulate standard python behaviour by disallowing duplicate names for args/kwargs.
                raise TypeError(
                    f"'build_custom_id' got multiple values for argument(s) '{', '.join(overlap)}'"
                )

            kwargs.update(args_as_kwargs)  # This is safe as we ensured there is no overlap.

        # "Serialize" types to str...
        deserialized_kwargs = {
            param.name: await param.to_str(kwargs[param.name]) for param in self.params
        }

        if self.regex:
            return self.id_spec.format(**deserialized_kwargs)
        return self.id_spec.format(sep=self.sep, **deserialized_kwargs)
