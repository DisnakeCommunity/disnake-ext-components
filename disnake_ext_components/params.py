from __future__ import annotations

import inspect
import re
import sys
import typing as t

import disnake
from disnake.ext.commands import params

from . import converter, exceptions, patterns, types_

if sys.version_info >= (3, 10):
    from types import NoneType, UnionType

    _UnionTypes = {t.Union, UnionType}
    _NoneTypes = {None, NoneType}

else:
    _UnionTypes = {t.Union}
    _NoneTypes = {None, type(None)}

__all__: t.List[str] = ["SelectValue", "ModalValue", "ParagraphModalValue"]


T = t.TypeVar("T")
ArgT = t.TypeVar("ArgT", bound=t.Union[t.List[str], str])

ConverterData = t.Tuple[
    t.List[t.Pattern[str]], t.Tuple[t.List[converter.ConverterSig], t.List[converter.ConverterSig]]
]
"""Parsed converter data."""


REGEX_MAP: t.Dict[type, t.Pattern[str]] = {
    # fmt: off
    str:                      patterns.STR,
    int:                      patterns.INT,
    float:                    patterns.FLOAT,
    bool:                     patterns.BOOL,
    disnake.User:             patterns.SNOWFLAKE,
    disnake.Member:           patterns.SNOWFLAKE,
    disnake.Role:             patterns.SNOWFLAKE,
    disnake.Thread:           patterns.SNOWFLAKE,
    disnake.TextChannel:      patterns.SNOWFLAKE,
    disnake.VoiceChannel:     patterns.SNOWFLAKE,
    disnake.CategoryChannel:  patterns.SNOWFLAKE,
    disnake.abc.GuildChannel: patterns.SNOWFLAKE,
    disnake.Guild:            patterns.SNOWFLAKE,
    disnake.Message:          patterns.SNOWFLAKE,
    disnake.Permissions:      patterns.STRICTINT,
    # disnake.Emoji:            ID,  # temporarily(?) disabled
    # fmt: on
}


class ParamInfo:
    """Helper class that stores information about a listener parameter. Mainly instantiated
    through `ParamInfo.from_param`. Contains the conversion strategy used to convert input
    to any of the parameter's annotated types.
    """

    param: inspect.Parameter
    """The listener parameter this :class:`ParamInfo` expands on."""

    converters_to: t.Tuple[converter.ConverterSig]
    """A list of converter functions used to convert the parameters. In param conversion,
    the converter is only called when the input argument matches the regex pattern.
    """

    converters_from: t.Tuple[converter.ConverterSig]
    """A list of converter functions used to convert the parameters. In param conversion,
    the converter is only called when the input argument matches the regex pattern.
    """

    regex: t.Tuple[t.Pattern[str]]
    """A list of all regex patterns used for input parameter conversion. In case regex matching
    is not necessary, this list will be empty.
    """

    def __init__(
        self,
        param: inspect.Parameter,
        *,
        converters_to: t.Optional[t.Sequence[converter.ConverterSig]] = None,
        converters_from: t.Optional[t.Sequence[converter.ConverterSig]] = None,
        regex: t.Optional[t.Sequence[t.Pattern[str]]] = None,
    ) -> None:
        self.param = param
        self.converters_to = () if converters_to is None else tuple(converters_to)
        self.converters_from = () if converters_from is None else tuple(converters_from)
        self.regex = () if regex is None else tuple(regex)

    @classmethod
    def from_param(cls, param: inspect.Parameter, validate: bool = True) -> ParamInfo:
        """Build a :class:`ParamInfo` from a given parameter.

        Parameters
        ----------
        param: :class:`inspect.Parameter`
            The parameter from which to build the :class:`ParamInfo`.
        """
        self = cls(param)

        regex, (converters_to, converters_from) = self.parse_annotation()
        self.converters_to += tuple(converters_to)
        self.converters_from += tuple(converters_from)
        if validate:
            self.regex += tuple(regex)

        return self

    def parse_annotation(
        self,
        annotation: t.Any = ...,
    ) -> ConverterData:
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

        if isinstance(annotation, types_.Converted):
            return self._parse_converted(annotation)

        if not (origin := types_.get_origin(annotation)):
            conv_to, conv_from = converter.CONVERTER_MAP[annotation]
            return [REGEX_MAP[annotation]], ([conv_to], [conv_from])

        elif origin in _UnionTypes:
            return self._parse_union(annotation)

        elif origin is t.Literal:
            return self._parse_literal(annotation)

        try:
            if issubclass(origin, t.Collection):
                # Ignore collection and parse first underlying type. Collection parsing is handled
                # by input to :meth:`self.convert` instead.
                return self.parse_annotation(
                    args[0] if (args := types_.get_args(annotation)) else str
                )

        except TypeError:
            pass

        raise TypeError(f"{annotation!r} is not a valid type annotation for a listener.")

    def _parse_union(self, annotation: t.Any) -> ConverterData:
        """Parse a :class:`typing.Union` annotation into the corresponding regex patterns and
        converter functions. Automatically removes any ``None``s from the union and sets
        :attr:`ParamInfo.default` to ``None`` if it is not yet set.
        """
        if types_.get_origin(annotation) in _UnionTypes:
            regex: t.List[t.Pattern[str]] = []
            conv_to: t.List[converter.ConverterSig] = []
            conv_from: t.List[converter.ConverterSig] = []

            for arg in types_.get_args(annotation):
                if arg in _NoneTypes:
                    if self.param.default is inspect.Parameter.empty:
                        self.param = self.param.replace(default=None)
                    continue

                arg_regex, (arg_conv_to, arg_conv_from) = self.parse_annotation(arg)
                regex += arg_regex
                conv_to += arg_conv_to
                conv_from += arg_conv_from

            return regex, (conv_to, conv_from)

        raise TypeError(f"{annotation!r} is not a valid typing.Union.")

    def _parse_literal(self, annotation: t.Any) -> ConverterData:
        """Parse a :class:`typing.Literal` annotation into the corresponding regex patterns and
        converter functions.
        """
        if types_.get_origin(annotation) is t.Literal:
            regex: t.List[t.Pattern[str]] = []
            conv_to: t.List[converter.ConverterSig] = []
            conv_from: t.List[converter.ConverterSig] = []

            for arg in types_.get_args(annotation):
                regex.append(re.compile(re.escape(str(arg))))
                arg_conv_to, arg_conv_from = converter.CONVERTER_MAP[type(arg)]
                conv_to.append(arg_conv_to)
                conv_from.append(arg_conv_from)

            return regex, (conv_to, conv_from)

        raise TypeError(f"{annotation!r} is not a valid typing.Literal.")

    def _parse_converted(self, annotation: types_.Converted) -> ConverterData:
        """Parse a :class:`.Converted` annotation into the corresponding regex patterns and
        converter functions.
        """
        return [annotation.regex], ([annotation.converter_to], [annotation.converter_from])

    @property
    def default(self) -> t.Any:
        """The default value of the parameter, used if all conversions fail. If this is
        `inspect.Parameter.empty`, this parameter is considered default-less, and thus required.
        """
        if isinstance(default := self.param.default, _ModalValue):
            return inspect.Parameter.empty if default.required else default.value
        elif isinstance(default, _SelectValue):
            lst: t.List[t.Any] = []
            return lst if default.min_values == 0 else inspect.Parameter.empty
        return default

    @property
    def optional(self) -> bool:
        """Whether or not this parameter is optional. If the parameter is default-less and optional,
        the parameter will instead default to `None`.
        """
        return self.default not in {inspect.Parameter.empty, Ellipsis}

    @property
    def name(self) -> str:
        """The name of the parameter."""
        return self.param.name

    @property
    def container_type(self) -> t.Optional[type]:
        """The container type, if any. For example, a parameter annotated as ``List[str]``
        would have container type ``list``.
        """
        annotation = self.param.annotation
        origin = t.get_origin(annotation) or annotation
        try:
            if issubclass(origin, t.Collection) and origin not in {str, bytes}:
                return t.cast(type, origin)
        except TypeError:
            pass
        return None

    @t.overload
    async def convert(self, argument: str, **kwargs: t.Any) -> t.Any:
        ...

    @t.overload
    async def convert(self, argument: t.List[str], **kwargs: t.Any) -> t.List[t.Any]:
        ...

    async def convert(
        self,
        argument: t.Union[t.List[str], str],
        **kwargs: t.Any,
    ) -> t.Union[t.List[t.Any], t.Any]:
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
        if not isinstance(argument, str):
            if not self.container_type:
                if len(argument) == 1:
                    return await self.convert(argument[0], **kwargs)

                exc = ValueError("Cannot convert a list of arguments to a non-collection type.")
                raise exceptions.ConversionError(
                    f"Failed to convert parameter {self.param.name}", self.param, [exc]
                )

            converted = [result for arg in argument for result in await self.convert(arg, **kwargs)]
            return self.container_type(converted)

        method = self._convert_and_validate if self.regex else self._convert_raw
        converted, errors = await method(argument, **kwargs)

        if not errors or self.optional:
            return self.container_type([converted]) if self.container_type else converted

        raise exceptions.ConversionError(
            f"Failed to convert parameter {self.param.name}", self.param, errors
        )

    async def _convert_raw(
        self, argument: str, **kwargs: t.Any
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Run converters on an argument without regex validation."""
        errors: t.List[ValueError] = []

        for conv in self.converters_to:
            try:
                return await self._actual_conversion(argument, conv, **kwargs)
            except ValueError as exc:
                errors.append(exc)

        return self.default, errors

    async def _convert_and_validate(
        self, argument: str, **kwargs: t.Any
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Run converters on an argument after validating that the argument
        can be of the correct type using regex.
        """
        match_cache: t.Set[t.Pattern[str]] = set()  # Prevent matching the same regex again.
        errors: t.List[ValueError] = []

        for regex, conv in zip(self.regex, self.converters_to):
            if regex not in match_cache:
                if regex.fullmatch(argument):
                    match_cache.add(regex)
                else:
                    errors.append(
                        exceptions.MatchFailure(
                            f"Input '{argument}' did not match r'{regex.pattern}'.",
                            self.param,
                            regex,
                        )
                    )
                    continue

            try:
                return await self._actual_conversion(argument, conv, **kwargs)
            except ValueError as exc:
                errors.append(exc)

        return self.default, errors

    async def _actual_conversion(
        self,
        argument: str,
        conv: converter.ConverterSig,
        **kwargs: t.Any,
    ) -> t.Tuple[t.Any, t.List[ValueError]]:
        """For internal use only. Actually run a converter on an argument and return the result.
        Raises whatever the converter function may raise. Generally speaking, this should only be
        :class:`ValueError`s.
        """
        converter_signature = params.signature(  # pyright: ignore
            conv.__new__ if isinstance(conv, type) else conv
        ).parameters

        converted = conv(
            argument,
            **{key: value for key, value in kwargs.items() if key in converter_signature},
        )

        if inspect.isawaitable(converted):
            return await converted, []
        return converted, []

    async def to_str(self, argument: t.Any) -> str:
        errors: t.List[ValueError] = []
        for conv in self.converters_from:
            try:
                converted = conv(argument)
                if inspect.isawaitable(converted):
                    return await converted
                return converted  # type: ignore  # Type not correctly narrowed.

            except ValueError as exc:
                errors.append(exc)

        raise exceptions.ConversionError(
            f"Failed to convert parameter {self.param.name}", self.param, errors
        )


class _SelectValue:
    def __init__(
        self,
        placeholder: t.Optional[str] = None,
        *,
        min_values: int = 1,
        max_values: t.Optional[int] = None,
        options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str], None] = None,
        disabled: bool = False,
    ):
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = options
        self.disabled = disabled

    def with_overrides(
        self,
        *,
        placeholder: t.Optional[str] = None,
        min_values: t.Optional[int] = None,
        max_values: t.Optional[int] = None,
        options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str], None] = None,
        disabled: t.Optional[bool] = None,
    ) -> _SelectValue:
        return type(self)(
            placeholder=self.placeholder if placeholder is None else placeholder,
            min_values=self.min_values if min_values is None else min_values,
            max_values=self.max_values if max_values is None else max_values,
            options=self.options if options is None else options,
            disabled=self.disabled if disabled is None else disabled,
        )

    def build(self, *, custom_id: str) -> disnake.ui.Select[t.Any]:
        options = self.options or []
        return disnake.ui.Select(
            custom_id=custom_id,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values or len(options),
            options=options,
            disabled=self.disabled,
        )


def SelectValue(
    placeholder: str,
    *,
    min_values: int = 1,
    max_values: t.Optional[int] = None,
    options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str], None] = None,
    disabled: bool = False,
) -> t.Any:
    return types_.AbstractComponent(
        type=disnake.ComponentType.select,
        placeholder=placeholder,
        min_values=min_values,
        max_values=max_values,
        options=options,
        disabled=disabled,
    )


class _ModalValue:
    def __init__(
        self,
        placeholder: t.Optional[str] = None,
        *,
        label: t.Optional[str] = None,
        value: t.Optional[str] = None,
        required: bool = True,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        style: disnake.TextInputStyle = disnake.TextInputStyle.short,
    ):
        self.placeholder = placeholder
        self.label = label
        self.value = value
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.style = style

    def with_overrides(
        self,
        *,
        placeholder: t.Optional[str] = None,
        label: t.Optional[str] = None,
        value: t.Optional[str] = None,
        required: t.Optional[bool] = None,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        style: disnake.TextInputStyle = disnake.TextInputStyle.short,
    ) -> _ModalValue:
        return type(self)(
            placeholder=self.placeholder if placeholder is None else placeholder,
            label=self.label if label is None else label,
            value=self.value if value is None else value,
            required=self.required if required is None else required,
            min_length=self.min_length if min_length is None else min_length,
            max_length=self.max_length if max_length is None else max_length,
            style=self.style if style is None else style,
        )

    def build(self, *, custom_id: str) -> disnake.ui.TextInput:
        return disnake.ui.TextInput(
            custom_id=custom_id,
            placeholder=self.placeholder,
            label=self.label or "\u200b",
            value=self.value,
            required=self.required,
            min_length=self.min_length,
            max_length=self.max_length,
            style=self.style,
        )


def ModalValue(
    placeholder: str,
    *,
    label: t.Optional[str] = None,
    value: t.Optional[str] = None,
    required: bool = True,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
    style: disnake.TextInputStyle = disnake.TextInputStyle.short,
) -> t.Any:
    return _ModalValue(
        placeholder,
        label=label,
        value=value,
        required=required,
        min_length=min_length,
        max_length=max_length,
        style=style,
    )


def ParagraphModalValue(
    placeholder: str,
    *,
    label: t.Optional[str] = None,
    value: t.Optional[str] = None,
    required: bool = True,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
) -> t.Any:
    return _ModalValue(
        placeholder,
        label=label,
        value=value,
        required=required,
        min_length=min_length,
        max_length=max_length,
        style=disnake.TextInputStyle.paragraph,
    )
