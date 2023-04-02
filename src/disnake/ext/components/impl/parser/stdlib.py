"""Parser implementations for types provided in the python standard library."""

from __future__ import annotations

import datetime
import enum  # Safe import, disnake imports this anyways.
import typing

import typing_extensions
from disnake.ext.components.impl.parser import base

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = (
    "NumberParser",
    "FloatParser",
    "IntParser",
    "BoolParser",
    "StringParser",
    "DatetimeParser",
    "DateParser",
    "TimeParser",
    "TimedeltaParser",
    "TimezoneParser",
)


_NumberT = typing_extensions.TypeVar("_NumberT", bound=float, default=float)


# INT / FLOAT


def _removesuffix(string: str, suffix: str) -> str:
    return string[: -len(suffix) if string.endswith(suffix) else None]


def dumps_float(number: float) -> str:
    """Dump a float to a string.

    Ensures trailing .0 are stripped to minimise float character length.
    """
    return _removesuffix(str(number), ".0")


class NumberParser(base.Parser[_NumberT]):
    """Base parser type for numbers.

    Defaults to a signed float parser.
    """

    type: typing.Union[typing.Type[int], typing.Type[float]]

    signed: bool
    base: int = 10

    @typing.overload
    def __new__(
        cls,
        *,
        decimal: typing.Literal[True] = True,
        signed: bool = True,
        base: int = 10,
    ) -> FloatParser:
        ...

    @typing.overload
    def __new__(
        cls,
        *,
        decimal: typing.Literal[False],
        signed: bool = True,
        base: int = 10,
    ) -> IntParser:
        ...

    def __new__(  # noqa: D102
        cls,
        *,
        decimal: bool = True,
        signed: bool = True,
        base: int = 10,
    ) -> typing.Union[FloatParser, IntParser]:
        if decimal and base != 10:
            msg = "FloatParsers must have base 10."
            raise TypeError(msg)

        self = super().__new__(FloatParser if decimal else IntParser)
        self.signed = signed
        self.base = base
        return self

    def check_sign(self, value: _NumberT) -> None:
        """Assert validity of a number for this parser.

        Parameters
        ----------
        value:
            The value to check

        Raises
        ------
        TypeError:
            The entered number was < 0 whereas this parser is for unsigned
            numbers (thus only numbers >= 0 are valid).
        """
        if not self.signed and value < 0:
            msg = "Unsigned numbers cannot be < 0."
            raise TypeError(msg)

    def loads(self, _: disnake.Interaction, argument: str) -> _NumberT:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        raise NotImplementedError

    def dumps(self, argument: _NumberT) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        raise NotImplementedError


class FloatParser(NumberParser[float], is_default_for=(float,)):
    """Specialised number parser for floats.

    This parser can be either signed or unsigned. The default float parser is
    signed.
    """

    type = float

    def __new__(cls, *, signed: bool = True) -> typing_extensions.Self:  # noqa: D102
        return super().__new__(cls, decimal=True, signed=signed, base=10)

    def loads(self, _: disnake.Interaction, argument: str) -> float:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        result = float(argument)
        self.check_sign(result)

        return result

    def dumps(self, argument: float) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return dumps_float(argument)


class IntParser(NumberParser[int], is_default_for=(int,)):
    """Specialised number parser for integers.

    This parser can be either signed or unsigned. The default float parser is
    signed.
    """

    type = int

    base: int

    def __new__(  # noqa: D102
        cls,
        *,
        signed: bool = True,
        base: int = 10,
    ) -> typing_extensions.Self:
        return super().__new__(cls, decimal=False, signed=signed, base=base)

    def loads(self, _: disnake.Interaction, argument: str) -> int:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        result = int(argument, self.base)
        self.check_sign(result)

        return result

    def dumps(self, argument: int) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return str(argument)


# BOOL

_DEFAULT_TRUES = frozenset(["true", "t", "yes", "y", "1"])
_DEFAULT_FALSES = frozenset(["false", "f", "no", "n", "0"])


class BoolParser(base.Parser[bool], is_default_for=(bool,)):
    """Parser type with support for bools.

    This parser type can be supplied with a collection of strings for the
    values that should be considered true and false. By default,
    ``"true", "t", "yes", "y", "1"`` are considered ``True``, while
    ``"false", "f", "no", "n", "0"`` are considered ``False``. Note that this
    is case-insensitive.
    """

    def __init__(
        self,
        trues: typing.Collection[str] = ...,
        falses: typing.Collection[str] = ...,
    ):
        self.trues = _DEFAULT_TRUES if trues is Ellipsis else trues
        self.falses = _DEFAULT_FALSES if falses is Ellipsis else falses

    def loads(self, _: disnake.Interaction, argument: str) -> bool:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        if argument in self.trues:
            return True
        elif argument in self.falses:
            return False

        trues_str = ", ".join(map(repr, self.trues))
        falses_str = ", ".join(map(repr, self.falses))
        msg = (
            f"Failed to parse {argument!r} into a bool. Expected any of"
            f" {trues_str} for True, or any of {falses_str} for False."
        )
        raise ValueError(msg)

    def dumps(self, argument: bool) -> str:  # noqa: D102, FBT001
        # NOTE: FBT001: Boolean trap is not relevant here, we're quite
        #               literally just dealing with a boolean.
        # <<docstring inherited from parser_api.Parser>>

        return "1" if argument else "0"


# STRING

StringParser = base.Parser.from_funcs(
    lambda _, arg: arg,
    str,
    is_default_for=(str,),
)


# DATETIME


class _Resolution(int, enum.Enum):
    """The resolution with which datetimes are stored."""

    MICROS = 1e-6
    SECONDS = 1
    MINUTES = 60 * SECONDS
    HOURS = 60 * MINUTES
    DAYS = 24 * HOURS


# TODO: Is forcing the use of timezones on users really a based move?
#       Probably.
class DatetimeParser(
    base.Parser[datetime.datetime], is_default_for=(datetime.datetime,)
):
    """Parser type with support for datetimes.

    Parameters
    ----------
    resolution:
        Dictates in how much detail the datetimes are stored inside strings.
        For example, a datetime object stored with resolution
        :attr:`DatetimeParser.res.DAYS` does not contain any information about
        hours/seconds/milliseconds/microseconds. Defaults to
        :attr:`DatetimeParser.res.SECONDS`.
    timezone:
        The timezone to use for parsing. Timezones returned by :meth:`loads`
        will always be of this timezone, and :meth:`dumps` will only accept
        datetimes of this timezone. Defaults to :obj:`datetime.timezone.utc`.
    """

    res = _Resolution

    def __init__(
        self,
        *,
        resolution: int = _Resolution.SECONDS,
        timezone: datetime.timezone = datetime.timezone.utc,
    ):
        self.resolution = resolution
        self.timezone = timezone

    def loads(  # noqa: D102
        self, _: disnake.Interaction, argument: str
    ) -> datetime.datetime:
        # <<docstring inherited from parser_api.Parser>>

        return datetime.datetime.fromtimestamp(float(argument), tz=self.timezone)

    def dumps(self, argument: datetime.datetime) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        if argument.tzinfo != self.timezone:
            msg = (
                "Cannot dump the provided datetime object due to a mismatch in"
                f" timezones. (expected: {self.timezone}, got: {argument.tzinfo})"
            )
            raise RuntimeError(msg)

        timestamp = argument.timestamp()
        if self.resolution == _Resolution.MICROS:
            return str(timestamp)

        return str(int(timestamp // self.resolution) * self.resolution)


DateParser = base.Parser.from_funcs(
    lambda _, arg: datetime.date.fromordinal(int(arg)),
    lambda arg: str(datetime.date.toordinal(arg)),
    is_default_for=(datetime.date,),
)


TimeParser = base.Parser.from_funcs(
    lambda _, arg: datetime.time.fromisoformat(arg),
    datetime.time.isoformat,
    is_default_for=(datetime.time,),
)


TimedeltaParser = base.Parser.from_funcs(
    lambda _, arg: datetime.timedelta(seconds=float(arg)),
    lambda arg: str(arg.total_seconds()),
    is_default_for=(datetime.timedelta,),
)


# NOTE: I assume seconds resolution for timezones is more than enough.
#       I would honestly assume even minutes are enough, though they
#       technically support going all the way down to microseconds.
TimezoneParser = base.Parser.from_funcs(
    lambda _, arg: datetime.timezone(datetime.timedelta(seconds=float(arg))),
    lambda arg: dumps_float(arg.utcoffset(None).total_seconds()),
    is_default_for=(datetime.timezone,),
)
