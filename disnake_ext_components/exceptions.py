import inspect
import re
import typing as t

from disnake.ext import commands

__all__ = ["ParserError", "MatchFailure", "ConversionError"]


class ParserError(commands.BadArgument, ValueError):
    """Base exception for errors related to listener param parsing."""

    message: str
    parameter: inspect.Parameter

    def __init__(self, message: str, parameter: inspect.Parameter) -> None:
        self.message = message
        self.parameter = parameter


class MatchFailure(ParserError):
    """Raised when a converter's regex failed to match."""

    regex: re.Pattern

    def __init__(
        self,
        message: str,
        parameter: inspect.Parameter,
        regex: re.Pattern,
    ) -> None:
        super().__init__(message, parameter)
        self.regex = regex


class ConversionError(ParserError):
    """Raised when conversion failed for a listener parameter.

    Parameters
    ----------
    message:
        The exception message.
    errors: Collection[Union[:class:`ValueError`, :class:`commands.BadArgument`]]
        All the exceptions that occured during parameter parsing and conversion.
    parameter: :class:`inspect.Parameter`
        The parameter for which conversion failed.
    """

    errors: t.Collection[t.Union[ValueError, commands.BadArgument]]
    parameter: inspect.Parameter

    def __init__(
        self,
        message: str,
        parameter: inspect.Parameter,
        exceptions: t.Iterable[t.Union[ValueError, commands.BadArgument]],
    ) -> None:
        super().__init__(message, parameter)
        self.exceptions = tuple(exceptions)
