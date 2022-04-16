from __future__ import annotations

import inspect
import typing as t

__all__ = ["ParserError", "MatchFailure", "ConversionError"]


class ParserError(ValueError):
    """Base exception for errors related to listener param parsing."""

    message: str
    parameter: inspect.Parameter

    def __init__(self, message: str, parameter: inspect.Parameter) -> None:
        self.message = message
        self.parameter = parameter


class MatchFailure(ParserError):
    """Raised when a converter's regex failed to match."""

    regex: t.Pattern[str]

    def __init__(
        self,
        message: str,
        parameter: inspect.Parameter,
        regex: t.Pattern[str],
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

    errors: t.Tuple[ValueError, ...]
    parameter: inspect.Parameter

    def __init__(
        self,
        message: str,
        parameter: inspect.Parameter,
        errors: t.Iterable[ValueError],
    ) -> None:
        super().__init__(message, parameter)
        self.errors = tuple(errors)
