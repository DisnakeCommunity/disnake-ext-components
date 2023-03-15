"""Protocols for parser types."""

from __future__ import annotations

import typing

import typing_extensions

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = ("Parser",)


_T = typing.TypeVar("_T")
_PT = typing_extensions.TypeVar("_PT", default=typing.Any)


MaybeCoroutine = typing.Union[_T, typing.Coroutine[None, None, _T]]


class Parser(typing.Protocol[_PT]):
    """The baseline protocol for any kind of parser.

    Any and all parser types must implement this protocol in order to be
    properly handled by disnake-ext-components.
    """

    __slots__: typing.Sequence[str] = ()

    def loads(
        self, __interaction: disnake.Interaction, __argument: object
    ) -> MaybeCoroutine[_PT]:
        """Load a value from a string and apply the necessary conversion logic.

        Any errors raised inside this method remain unmodified, and should be
        handled externally.

        Parameters
        ----------
        interaction:
            The interaction in the context of which the argument should be
            parsed. For example, parsing a :class:`disnake.Member` could use
            the interaction to determine the guild from which the member should
            be derived.
        argument:
            The argument to parse into the desired type.
        """
        ...

    def dumps(self, __argument: _PT) -> MaybeCoroutine[str]:
        """Dump a value from a given type and convert it to a string.

        In most cases, it is imperative to ensure that this is done in a
        reversible way, such that calling :meth:`loads` on the result of this
        function should return the same result. For example:

        .. code-block:: python3
            >>> parser = IntParser()
            >>> input_str = "1"
            >>> parsed_int = parser.loads(input_str)
            >>> dumped_int = parser.dumps(parsed_int)
            >>> input_str == dumped_int
            True

        Any errors raised inside this method remain unmodified, and should be
        handled externally.

        Parameters
        ----------
        interaction:
            The interaction in the context of which the argument should be
            parsed. For example, parsing a :class:`disnake.Member` could use
            the interaction to determine the guild from which the member should
            be derived.
        argument:
            The argument to parse into the desired type.
        """
        ...
