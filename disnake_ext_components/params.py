from __future__ import annotations

import inspect
import re
import sys
import typing as t

import disnake
from disnake.ext.commands import params

from . import converter, exceptions

if sys.version_info >= (3, 10):
    import types

    _UnionTypes = {t.Union, types.UnionType}
    _NoneTypes = {None, types.NoneType}

else:
    _UnionTypes = {t.Union}
    _NoneTypes = {None, type(None)}


ID = re.compile(r"\d{15,20}")

# flake8: noqa: E241
REGEX_MAP: t.Dict[type, re.Pattern] = {
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


class ParamInfo:
    """Helper class that stores information about a listener parameter. Mainly instantiated
    through `ParamInfo.from_param`. Contains the conversion strategy used to convert input
    to any of the parameter's annotated types.
    """

    param: inspect.Parameter
    """The listener parameter this :class:`ParamInfo` expands on."""

    converters: t.List[converter.ConverterSig]
    """A list of converter functions used to convert the parameters. In param conversion,
    the converter is only called when the input argument matches the regex pattern.
    """

    regex: t.List[re.Pattern]
    """A list of all regex patterns used for input parameter conversion. In case regex matching
    is not necessary, this list will be empty.
    """

    def __init__(
        self,
        param: inspect.Parameter,
        *,
        converters: t.Optional[t.List[converter.ConverterSig]] = None,
        regex: t.Optional[t.List[converter.ConverterSig]] = None,
    ) -> None:
        self.param = param
        self.converters = [] if converters is None else converters
        self.regex = [] if regex is None else regex

    @classmethod
    def from_param(cls, param: inspect.Parameter, validate: bool = True) -> ParamInfo:
        """Build a :class:`ParamInfo` from a given parameter.

        Parameters
        ----------
        param: :class:`inspect.Parameter`
            The parameter from which to build the :class:`ParamInfo`.
        """
        self = cls(param)

        regex, converters = self.parse_annotation()
        self.converters.extend(converters)
        if validate:
            self.regex.extend(regex)

        return self

    def parse_annotation(
        self,
        annotation: t.Any = ...,
    ) -> t.Tuple[t.List[re.Pattern], t.List[converter.ConverterSig]]:
        """Parse a conversion strategy from a function parameter annotation. This includes a list
        of :class:`re.Pattern`s and a list of converter functions. These will be sequentially
        traversed for argument conversion.

        Parameters
        ----------
        annotation: :class:`inspect.Parameter`
            The parameter for which the converters are to be parsed.

        Raises
        ------
        TypeError:
            The parameter is annotated such that it failed to parse.
            Valid annotations incluce :class:`str` / :class:`int` / :class:`float` / :class:`bool`,
            most disnake types, :class:`typing.Optional`s and :class:`typing.Union`s of these
            types, and :class:`typing.Literal`s.
        KeyError:
            A parameter is annotated with a type for which no converter exists.

        Returns
        -------
        Tuple[List[:class:`re.Pattern`], List[:class:`ConverterSig`]]:
            A tuple containing:
            - a list of patterns against which the `custom_id` component will be matched,
            - a list of converter functions used to convert input to a different type.
        """
        if annotation is Ellipsis:
            annotation = self.param.annotation

        if annotation is inspect.Parameter.empty:
            annotation = str

        if not (origin := t.get_origin(annotation)):
            return [REGEX_MAP[annotation]], [converter.CONVERTER_MAP[annotation]]

        elif origin in _UnionTypes:
            return self._parse_union(annotation)

        elif origin is t.Literal:
            return self._parse_literal(annotation)

        elif origin is params.Injection:
            raise NotImplementedError("Injections are not yet implemented. Soon:tm:")

        raise TypeError(f"{type!r} is not a valid type annotation for a listener.")

    def _parse_union(
        self, annotation: t.Any
    ) -> t.Tuple[t.List[re.Pattern], t.List[converter.ConverterSig]]:

        if t.get_origin(annotation) in _UnionTypes:
            regex, conv = [], []
            for arg in t.get_args(annotation):
                if arg in _NoneTypes:
                    if self.param.default is inspect.Parameter.empty:
                        self.param = self.param.replace(default=None)
                    continue

                arg_regex, arg_conv = self.parse_annotation(arg)
                regex += arg_regex
                conv += arg_conv
            return regex, conv

        raise TypeError(f"{annotation!r} is not a valid typing.Union.")

    def _parse_literal(
        self, annotation: t.Any
    ) -> t.Tuple[t.List[re.Pattern], t.List[converter.ConverterSig]]:

        if t.get_origin(annotation) is t.Literal:
            regex, conv = [], []
            for arg in t.get_args(annotation):
                regex.append(re.compile(re.escape(str(arg))))
                conv.append(converter.CONVERTER_MAP[type(arg)])
            return regex, conv

        raise TypeError(f"{annotation!r} is not a valid typing.Literal.")

    @property
    def default(self) -> t.Any:
        """The default value of the parameter, used if all conversions fail. If this is
        `inspect.Parameter.empty`, this parameter is considered default-less.
        """
        return self.param.default

    @property
    def optional(self) -> bool:
        """Whether or not this parameter is optional. If the parameter is default-less and optional,
        the parameter will instead default to `None`.
        """
        return self.default is not inspect.Parameter.empty

    async def convert(self, argument: str, **kwargs: t.Any) -> t.Any:
        """Try to convert an input argument for this command into any of its annotated types.
        Conversion results are returned as soon as the first converter passes. To this end, the
        order in which types were annotated in e.g. a :class:`typing.Union` is preserved.

        Parameters
        ----------
        argument: :class:`str`
            The input argument that is to be converted.
        validate: :class:`bool`
            Whether or not to run a regex match before attempting a converter. Defaults to `True`.
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
        method = self._convert_and_validate if self.regex else self._convert_raw
        converted, errors = await method(argument, **kwargs)

        if not errors or self.optional:
            return converted

        raise exceptions.ConversionError(
            f"Failed to convert parameter {self.param.name}", self.param, errors
        )

    async def _convert_raw(
        self, argument: str, **kwargs: t.Any
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Run converters on an argument without regex validation."""
        errors: t.List[ValueError] = []

        for converter in self.converters:
            try:
                return await self._actual_conversion(argument, converter, **kwargs)
            except ValueError as exc:
                errors.append(exc)

        return self.default, errors

    async def _convert_and_validate(
        self, argument: str, **kwargs: t.Any
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Run converters on an argument after validating that the argument
        can be of the correct type using regex.
        """
        match_cache: t.Set[re.Pattern] = set()  # Prevent matching the same regex again.
        errors: t.List[ValueError] = []

        for regex, converter in zip(self.regex, self.converters):
            if regex not in match_cache:
                if regex.fullmatch(argument):
                    match_cache.add(regex)
                else:
                    errors.append(
                        exceptions.MatchFailure(
                            f"Input '{argument}' did not match {regex.pattern}.", self.param, regex
                        )
                    )
                    continue

            try:
                return await self._actual_conversion(argument, converter, **kwargs)
            except ValueError as exc:
                errors.append(exc)

        return self.default, errors

    async def _actual_conversion(
        self,
        argument: str,
        converter: converter.ConverterSig,
        **kwargs: t.Any,
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Actually run a converter on an argument and return the result.
        Raises whatever the converter function may raise. Generally speaking, this should only be
        :class:`ValueError`s.
        """
        print(converter)
        converter_signature = params.signature(
            converter.__new__ if isinstance(converter, type) else converter
        ).parameters

        converted = converter(
            argument,
            **{key: value for key, value in kwargs.items() if key in converter_signature},
        )

        if inspect.isawaitable(converted):
            return await converted, []
        return converted, []
