from __future__ import annotations

import inspect
import re
import sys
import typing as t

import disnake
from disnake.ext import commands
from disnake.ext.commands import converter as dpy_converter
from disnake.ext.commands import params

from . import exceptions

if sys.version_info >= (3, 10):
    import types

    _UnionTypes = {t.Union, types.UnionType}
    _NoneTypes = {None, types.NoneType}

else:
    _UnionTypes = {t.Union}
    _NoneTypes = {None, type(None)}


# TODO: Maybe rework converters, will leave as-is for now until I think of something better
ConverterSig = t.Union[
    t.Callable[..., t.Awaitable[t.Any]],
    t.Callable[..., t.Any],
]


ID = re.compile(r"\d{15,20}")
REGEX_MAP: t.Dict[type, re.Pattern[str]] = {
    # fmt: off
    str:                      re.compile(r".*"),
    int:                      re.compile(r"-?\d+"),
    float:                    re.compile(r"[-+]?(?:\d*\.\d+|\d+)"),
    bool:                     re.compile(r"true|false|t|f|yes|no|y|n|1|0|enable|disable|on|off", re.I),
    disnake.User:             ID,
    disnake.Member:           ID,
    disnake.Role:             ID,
    disnake.Thread:           ID,
    disnake.TextChannel:      ID,
    disnake.VoiceChannel:     ID,
    disnake.CategoryChannel:  ID,
    disnake.abc.GuildChannel: ID,
    disnake.Guild:            ID,
    disnake.Message:          ID,
    disnake.Emoji:            ID,
    # fmt: on
}


def async_converter(converter: t.Callable[[str], t.Any]) -> ConverterSig:
    """Transform a simple callable into an async converter. Though this is independent of the
    interaction, it is still provided in the signature to keep converters consistent.
    """

    async def convert(inter: disnake.MessageInteraction, argument: str) -> t.Any:
        try:
            return converter(argument)
        except Exception as exc:
            raise commands.BadArgument(
                f"Failed to convert input '{argument}' to type '{converter.__name__}'"
            ) from exc

    return convert


CONVERTER_MAP: t.Mapping[type, ConverterSig] = {
    # fmt: off
    str:                      async_converter(str),
    int:                      async_converter(int),
    float:                    async_converter(float),
    bool:                     async_converter(dpy_converter._convert_to_bool),
    disnake.User:             dpy_converter.UserConverter().convert,
    disnake.Member:           dpy_converter.MemberConverter().convert,
    disnake.Role:             dpy_converter.RoleConverter().convert,
    disnake.Thread:           dpy_converter.ThreadConverter().convert,
    disnake.TextChannel:      dpy_converter.TextChannelConverter().convert,
    disnake.VoiceChannel:     dpy_converter.VoiceChannelConverter().convert,
    disnake.CategoryChannel:  dpy_converter.CategoryChannelConverter().convert,
    disnake.abc.GuildChannel: dpy_converter.GuildChannelConverter().convert,
    disnake.Guild:            dpy_converter.GuildConverter().convert,
    disnake.Message:          dpy_converter.MessageConverter().convert,
    disnake.Emoji:            dpy_converter.EmojiConverter().convert,
    # fmt: on
}


def parse_param(param: inspect.Parameter) -> t.Mapping[re.Pattern[str], ConverterSig]:
    """Parse a conversion strategy from a function parameter. This is a mapping of
    regex patterns to converter functions.

    Parameters
    ----------
    param: :class:`inspect.Parameter`
        The parameter for which the converters are to be parsed.

    Raises
    ------
    TypeError:
        The parameter is annotated such that it failed to parse.
        Currently valid options include str/int/float/bool, most disnake types,
        Optionals and Unions of these types, and Literals.
    KeyError:
        A parameter is annotated with a type for which no converter exists.

    Returns
    -------
    List[:class:`re.Pattern`]:
        A list of patterns against which the `custom_id` component will be matched.
    """
    if (annotation := param.annotation) is inspect.Parameter.empty:
        return {REGEX_MAP[str]: CONVERTER_MAP[str]}

    args = t.get_args(annotation)
    if not (origin := t.get_origin(annotation)):
        return {REGEX_MAP[annotation]: CONVERTER_MAP[annotation]}

    elif origin in _UnionTypes:
        return {REGEX_MAP[tp]: CONVERTER_MAP[tp] for tp in args if tp not in _NoneTypes}

    elif origin is t.Literal:
        return {re.compile(re.escape(str(arg))): CONVERTER_MAP[type(arg)] for arg in args}

    else:
        raise TypeError(f"Cannot create a suitable regex pattern for parameter {param.name}.")


def is_optional(param: inspect.Parameter) -> bool:
    """Check whether or not a parameter is optional. A parameter is deemed optional when it has a
    default set, or it is annotated as `typing.Optional[...]` or `typing.Union[None, ...]`.

    Parameters
    ----------
    param: :class:`inspect.Parameter`
        The parameter of which to check whether it is optional.

    Returns
    -------
    bool:
        True if the parameter is optional, False otherwise.
    """
    if param.default is not inspect.Parameter.empty:
        return True

    if args := t.get_args(param.annotation):
        return bool(_NoneTypes.intersection(args))

    return False


class ParamInfo:
    """Helper class that stores information about a listener parameter. Mainly instantiated
    through `ParamInfo.from_param`. Contains the conversion strategy used to convert input
    to any of the parameter's annotated types.
    """

    param: inspect.Parameter
    """The listener parameter this :class:`ParamInfo` expands on."""

    converter_mapping: t.Mapping[re.Pattern[str], ConverterSig]
    """A mapping of a regex pattern to a converter function. In param conversion,
    the converter is only called when the input argument matches the regex pattern.
    """

    default: t.Any
    """The default value of the parameter, used if all conversions fail. If this is
    `inspect.Parameter.empty`, this parameter is considered default-less.
    """

    optional: bool
    """Whether or not this parameter is optional. If the parameter is default-less and optional,
    the parameter will instead default to `None`.
    """

    def __init__(
        self,
        param: inspect.Parameter,
        *,
        converter_mapping: t.Mapping[re.Pattern[str], ConverterSig],
    ) -> None:
        self.param = param
        self.converter_mapping = converter_mapping
        self.default = param.default
        self.optional = is_optional(param)

    @classmethod
    def from_param(cls, param: inspect.Parameter) -> ParamInfo:
        """Build a :class:`ParamInfo` from a given parameter.

        Parameters
        ----------
        param: :class:`inspect.Parameter`
            The parameter from which to build the :class:`ParamInfo`.
        """
        return cls(param, converter_mapping=parse_param(param))

    @property
    def regex(self) -> t.Tuple[re.Pattern[str], ...]:
        """A tuple of all regex patterns used for input argument conversion."""
        return tuple(self.converter_mapping)

    @property
    def converters(self) -> t.Tuple[ConverterSig, ...]:
        """A tuple of all converter functions used for input argument conversion."""
        return tuple(self.converter_mapping.values())

    async def convert(
        self,
        argument: str,
        *,
        skip_validation: bool = False,
        **kwargs: t.Any,
    ) -> t.Any:
        """Try to convert an input argument for this command into any of its annotated types.
        Conversion results are returned as soon as the first converter passes. To this end, the
        order in which types were annotated in e.g. a :class:`typing.Union` is preserved.

        Parameters
        ----------
        argument: :class:`str`
            The input argument that is to be converted.
        skip_validation: :class:`bool`
            Whether or not to skip regex matching before attempting a converter.
        **kwargs: :class:`typing.Any`
            Any other external values that are to be forwarded to the converter. In case extra
            parameters are passed that the converter doesn't support, these are silently ignored.

        Raises
        ------
        :class:`exceptions.ConversionError`:
            All converters failed for the given input argument. All individual conversion errors
            that occured during conversions are stored inside this exception. In case any other
            type of exception is raised, some unexpected error occurred during conversion instead.

        Returns
        :class:`typing.Any`:
            The successfully converted input argument.
        """

        match_cache: t.Set[re.Pattern[str]] = set()  # Prevent matching the same regex again.
        errors: t.List[t.Union[commands.BadArgument, ValueError]] = []

        # Try converters
        for regex, converter in self.converter_mapping.items():
            if not skip_validation:
                if regex in match_cache:
                    pass
                elif regex.fullmatch(argument):
                    match_cache.add(regex)
                else:
                    errors.append(
                        exceptions.MatchFailure(
                            f"Input '{argument}' did not match {regex.pattern}.", self.param, regex
                        )
                    )
                    continue

            try:
                converter_signature = params.signature(converter).parameters
                return await converter(
                    argument=argument,
                    **{key: value for key, value in kwargs.items() if key in converter_signature},
                )
            except (commands.BadArgument, ValueError) as exc:
                errors.append(exc)

        # Conversions failed, return default or raise
        if self.optional:
            return None if self.default is inspect.Parameter.empty else self.default

        raise exceptions.ConversionError(
            f"Failed to convert parameter {self.param.name}", self.param, errors
        )
