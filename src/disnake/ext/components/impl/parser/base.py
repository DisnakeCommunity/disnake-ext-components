"""Implementation of parser base classes upon which actual parsers are built."""

from __future__ import annotations

import types
import typing

from disnake.ext.components.api import parser as parser_api

if typing.TYPE_CHECKING:
    import disnake
    import typing_extensions

__all__: typing.Sequence[str] = (
    "register_parser",
    "get_parser",
    "Parser",
)

_PARSERS: typing.Dict[typing.Type[typing.Any], typing.Type[Parser[typing.Any]]] = {}


_T = typing.TypeVar("_T")

MaybeCoroutine = typing.Union[typing.Coroutine[None, None, _T], _T]
TypeSequence = typing.Sequence[typing.Type[typing.Any]]


def register_parser(
    parser: typing.Type[Parser[_T]],
    *types: typing.Type[_T],
    force: bool = True,
) -> None:
    """Register a parser class as the default parser for the provided type.

    The default parser will automatically be used for any field annotated
    with that type. For example, the default parser for integers is
    :class:`components.IntParser`, an instance of which will automatically be
    assigned to any custom id fields annotated with `int`.

    Parameters
    ----------
    parser:
        The parser to register.
    types:
        The types for which to register the provided parser as the default.
    force:
        Whether or not to overwrite existing defaults. Defaults to ``True``.
    """
    strategy = _PARSERS.__setitem__ if force else _PARSERS.setdefault

    for type in types:
        strategy(type, parser)


def get_parser(type_: typing.Type[_T]) -> typing.Type[Parser[_T]]:
    """Get the default parser for the provided type.

    Parameters
    ----------
    type_:
        The type for which to return the default parser.

    Returns
    -------
    typing.Type[:class:`Parser`]:
        The default parser class for the provided type.

    Raises
    ------
    KeyError:
        The provided type has no registered parser.
    """
    # TODO: Somehow allow more flexibility here. It would at the very least
    #       be neat to be able to pick between strictly sync/async parsers
    #       (mainly for the purpose of not making api requests); but perhaps
    #       allowing the user to pass a filter function could be cool?
    return _PARSERS[type_]


class Parser(parser_api.Parser[_T], typing.Protocol[_T]):
    """Class that handles parsing of one custom id field to and from a desired type.

    A parser contains two main methods, :meth:`loads` and :meth:`dumps`.
    ``loads``, like :func:`json.loads` serves to turn a string value into
    a different type. Similarly, ``dumps`` serves to convert that type
    back into a string.

    Simpler parsers can also be generated from ``loads`` and ``dumps`` functions
    using :meth:`from_funcs`, so as to not have to define an entire class.
    """

    def __init_subclass__(
        cls,
        *,
        is_default_for: typing.Optional[TypeSequence] = None,
        **kwargs: object,
    ) -> None:
        # Allows defining a parser with `is_default_for=[type1, ...]` to
        # auto-register the parser for the provided types to reduce
        # boilerplate.
        super().__init_subclass__(**kwargs)
        if is_default_for:
            register_parser(cls, *is_default_for)

    @classmethod
    def default(cls) -> typing_extensions.Self:
        """Return the default implementation of this parser type.

        By default, this will just create the parser class with no arguments,
        but this can be overwritten on child classes for customised behaviour.

        Returns
        -------
        Parser:
            The default parser instance for this parser type.
        """
        return cls()

    @classmethod
    def from_funcs(
        cls,
        loads: typing.Callable[[disnake.Interaction, str], MaybeCoroutine[_T]],
        dumps: typing.Callable[[_T], MaybeCoroutine[str]],
        *,
        is_default_for: typing.Optional[TypeSequence] = None,
    ) -> typing.Type[typing_extensions.Self]:
        """Generate a parser class from ``loads`` and ``dumps`` functions.

        Note that these ``loads`` and ``dumps`` functions must **not** have
        a ``self`` argument. They are treated as static methods. If a ``self``
        argument is required, consider making a parser class through
        inheritance instead.

        Parameters
        ----------
        loads:
            A function that serves to turn a string value into a different type,
            similar to :func:`json.loads`.
        dumps:
            A function that serves to turn a value of a given type back into a
            string, similar to :func:`json.dumps`.
        is_default_for:
            The types for which to register the newly created parser class as
            the default parser. By default, the parser is not registered as the
            default for any types.

        Returns
        -------
        typing.Type[:class:`Parser`]:
            The newly created parser class.
        """
        new_cls = typing.cast(
            "typing.Type[typing_extensions.Self]",
            types.new_class(
                f"{type.__name__}Parser",
                (cls,),
                {"is_default_for": is_default_for},
            ),
        )

        # XXX: Not really type-safe whatsoever but it'll suffice.
        new_cls.loads = staticmethod(loads)  # pyright: ignore
        new_cls.dumps = staticmethod(dumps)  # pyright: ignore

        return new_cls

    def loads(  # noqa: D102
        self, __interaction: disnake.Interaction, __argument: str
    ) -> MaybeCoroutine[_T]:
        # <<Docstring inherited from parser_api.Parser>>
        ...

    def dumps(self, __argument: _T) -> MaybeCoroutine[str]:  # noqa: D102
        # <<Docstring inherited from parser_api.Parser>>
        ...
