import datetime
import inspect
import typing as t

import disnake
import pytest

import disnake_ext_components as components

ParsedParams = t.Tuple[t.Tuple[inspect.Parameter, ...], t.Tuple[inspect.Parameter, ...]]


utc = datetime.timezone.utc


@pytest.fixture
def button_params(button_listener_callback: t.Callable[..., t.Any]) -> ParsedParams:
    sig = inspect.signature(button_listener_callback)
    return components.utils.extract_listener_params(sig)


def param_from_annotation(
    annotation: t.Any,
    # *,
    default: t.Any = inspect._empty,
) -> inspect.Parameter:
    """Create a fake parameter to validate against."""
    return inspect.Parameter(
        "x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation, default=default
    )


# params.ParamInfo.name


def test_paraminfo_name():
    def something(foo: str, bar: str, baz: str, bat: str):
        ...

    sig = inspect.signature(something)
    assert all(
        name == components.params.ParamInfo.from_param(param).name
        for name, param in sig.parameters.items()
    )


# params.ParamInfo.convert


@pytest.mark.asyncio
async def test_paraminfo_convert_single():
    param = param_from_annotation(str)
    paraminfo = components.params.ParamInfo.from_param(param)

    assert await paraminfo.convert("abc") == "abc"
    assert await paraminfo.convert("123") == "123"


@pytest.mark.asyncio
async def test_paraminfo_convert_multi():
    param = param_from_annotation(t.List[str])
    paraminfo = components.params.ParamInfo.from_param(param)

    assert await paraminfo.convert(["abc", "def"]) == ["abc", "def"]


@pytest.mark.asyncio
async def test_paraminfo_convert_fail_single():
    param = param_from_annotation(int)
    paraminfo = components.params.ParamInfo.from_param(param)

    with pytest.raises(components.ConversionError):
        await paraminfo.convert("abc")


@pytest.mark.asyncio
async def test_paraminfo_convert_fail_multi():
    param = param_from_annotation(t.List[int])
    paraminfo = components.params.ParamInfo.from_param(param)

    with pytest.raises(components.ConversionError) as exc_info:
        await paraminfo.convert(["123", "def"])

    # For good measure, ensure the first one matched and only the second one errored.
    assert len(exc_info.value.errors) == 1
    assert isinstance(exc := exc_info.value.errors[0], components.MatchFailure)
    assert exc.message == f"Input 'def' did not match r'{components.patterns.INT.pattern}'."


@pytest.mark.asyncio
async def test_paraminfo_convert_skip_validation():
    param = param_from_annotation(int)
    paraminfo = components.params.ParamInfo.from_param(param, validate=False)

    assert await paraminfo.convert("123") == 123

    # Confirm that, when converting an incorrect value, it errors on conversion instead
    # of during matching.
    with pytest.raises(components.ConversionError) as exc_info:
        await paraminfo.convert("abc")

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].args == ("invalid literal for int() with base 10: 'abc'",)


# params.ParamInfo | empty


@pytest.mark.asyncio
async def test_str_paraminfo():
    param = param_from_annotation(inspect.Parameter.empty)
    paraminfo = components.params.ParamInfo.from_param(param)

    assert param == paraminfo.param

    assert await paraminfo.convert("123") == "123"
    assert await paraminfo.convert("True") == "True"


# params.ParamInfo | t.Optional


@pytest.mark.asyncio
async def test_optional_paraminfo_no_default():
    param = param_from_annotation(t.Optional[int])
    paraminfo = components.params.ParamInfo.from_param(param)

    # x: Optional[int] -> x: Optional[int] = None
    assert param.replace(default=None) == paraminfo.param

    assert paraminfo.default is None
    assert paraminfo.optional is True

    assert await paraminfo.convert("1234") == 1234
    assert await paraminfo.convert("abcd") is None
    assert await paraminfo.convert("") is None


@pytest.mark.asyncio
async def test_optional_paraminfo_with_default():
    default = 3
    param = param_from_annotation(t.Optional[int], default=default)
    paraminfo = components.params.ParamInfo.from_param(param)

    # x: Optional[int] = 3 -> x: Optional[int] = 3  # ...ensure this isn't overwritten
    assert param == paraminfo.param

    assert paraminfo.default == 3
    assert paraminfo.optional is True

    assert await paraminfo.convert("1234") == 1234
    assert await paraminfo.convert("abcd") == default
    assert await paraminfo.convert("") == default


# params.ParamInfo | t.Union


@pytest.mark.asyncio
async def test_union_paraminfo():
    param = param_from_annotation(t.Union[int, bool])
    paraminfo = components.params.ParamInfo.from_param(param)

    assert param == paraminfo.param

    assert await paraminfo.convert("t") is True
    assert await paraminfo.convert("6") == 6

    # int before bool -> int takes priority
    assert 1 == await paraminfo.convert("1") is not True

    # Ensure the reverse holds true...
    param_switched = param_from_annotation(t.Union[bool, int])
    paraminfo_switched = components.params.ParamInfo.from_param(param_switched)

    assert await paraminfo_switched.convert("1") is True


# params.ParamInfo | t.Literal


@pytest.mark.asyncio
async def test_literal_paraminfo():
    param = param_from_annotation(t.Literal[1, "a", True])
    paraminfo = components.params.ParamInfo.from_param(param)

    assert param == paraminfo.param

    assert await paraminfo.convert("True") is True
    assert await paraminfo.convert("a") == "a"
    assert await paraminfo.convert("1") == 1

    with pytest.raises(components.ConversionError):
        await paraminfo.convert("something else")


# params.ParamInfo | t.Collection


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "annotation, expected",
    (
        (t.Set[int], {1, 2, 3}),
        (t.List[int], [1, 2, 3]),
        (t.Tuple[int], (1, 2, 3)),
    ),
)
async def test_collection_paraminfo(annotation: t.Any, expected: t.Collection[int]):
    param = param_from_annotation(annotation)
    # param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
    paraminfo = components.params.ParamInfo.from_param(param)

    assert param == paraminfo.param

    assert not paraminfo.optional

    assert await paraminfo.convert(["1", "2", "3"]) == expected


# params.ParamInfo | components.Converted


def to_datetime(arg: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(int(arg), tz=utc)


def from_datetime(arg: datetime.datetime) -> str:
    return str(int(arg.timestamp()))


async def to_datetime_async(arg: str) -> datetime.datetime:
    return to_datetime(arg)


async def from_datetime_async(arg: datetime.datetime) -> str:
    return from_datetime(arg)


@pytest.mark.asyncio
@pytest.mark.parametrize("conv_to", (to_datetime, to_datetime_async))
@pytest.mark.parametrize("conv_from", (from_datetime, from_datetime_async))
async def test_converted_paraminfo(
    conv_to: t.Callable[..., t.Any], conv_from: t.Callable[..., t.Any]
):
    param = param_from_annotation(
        components.Converted[components.patterns.STRICTINT, conv_to, conv_from]
    )
    paraminfo = components.params.ParamInfo.from_param(param)

    assert param == paraminfo.param

    assert await paraminfo.convert("0") == (dt := datetime.datetime(1970, 1, 1, tzinfo=utc))
    assert await paraminfo.to_str(dt) == "0"


# params.ParamInfo | exc


def test_fail_converter_map_paraminfo():
    param = param_from_annotation(datetime.datetime)
    with pytest.raises(KeyError):
        components.params.ParamInfo.from_param(param)


def test_fail_unsupported_type_paraminfo():
    param = param_from_annotation(t.ClassVar[int])
    with pytest.raises(TypeError):
        components.params.ParamInfo.from_param(param)


# params.ParamInfo | fail conversion


# params.SelectValue


def test_selectvalue():
    kwargs = {
        "placeholder": "blablabla",
        "min_values": "2",
        "max_values": "4",
        "options": ["a", "b", "c", "d", "e"],
        "disabled": True,
    }

    from_cls = components.params._SelectValue(**kwargs)  # type: ignore
    from_func = components.SelectValue(**kwargs)  # type: ignore

    assert from_cls.placeholder == from_func.placeholder == kwargs["placeholder"]
    assert from_cls.min_values == from_func.min_values == kwargs["min_values"]
    assert from_cls.max_values == from_func.max_values == kwargs["max_values"]
    assert from_cls.options == from_func.options == kwargs["options"]
    assert from_cls.disabled == from_func.disabled == kwargs["disabled"]


# params.ModalValue


def test_modalvalue():
    kwargs = {
        "placeholder": "blablabla",
        "label": "something",
        "value": "something else",
        "required": False,
        "min_length": 123,
        "max_length": 456,
    }

    short = disnake.TextInputStyle.short
    long = disnake.TextInputStyle.paragraph

    from_cls_short = components.params._ModalValue(**kwargs)  # type: ignore
    from_func_short = components.ModalValue(**kwargs)  # type: ignore

    assert from_cls_short.placeholder == from_func_short.placeholder == kwargs["placeholder"]
    assert from_cls_short.label == from_func_short.label == kwargs["label"]
    assert from_cls_short.value == from_func_short.value == kwargs["value"]
    assert from_cls_short.required == from_func_short.required == kwargs["required"]
    assert from_cls_short.min_length == from_func_short.min_length == kwargs["min_length"]
    assert from_cls_short.max_length == from_func_short.max_length == kwargs["max_length"]
    assert from_cls_short.style == from_func_short.style == short

    from_cls_long = components.params._ModalValue(style=long, **kwargs)  # type: ignore
    from_func_long = components.ParagraphModalValue(**kwargs)  # type: ignore

    assert from_cls_long.placeholder == from_func_long.placeholder == kwargs["placeholder"]
    assert from_cls_long.label == from_func_long.label == kwargs["label"]
    assert from_cls_long.value == from_func_long.value == kwargs["value"]
    assert from_cls_long.required == from_func_long.required == kwargs["required"]
    assert from_cls_long.min_length == from_func_long.min_length == kwargs["min_length"]
    assert from_cls_long.max_length == from_func_long.max_length == kwargs["max_length"]
    assert from_cls_long.style == from_func_long.style == long
