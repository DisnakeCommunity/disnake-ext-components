import inspect
import re
import typing as t

import pytest

import disnake_ext_components as components

# utils.ensure_compiled


def test_compile():
    pat = components.utils.ensure_compiled("abc")

    assert pat.pattern == "abc"
    assert pat.flags == re.UNICODE


def test_compile_flag():
    pat = components.utils.ensure_compiled("abc", flags=re.DOTALL | re.IGNORECASE)

    assert pat.pattern == "abc"
    assert pat.flags == re.DOTALL | re.IGNORECASE | re.UNICODE


def test_precompiled():
    pre_pat = re.compile("abc")
    pat = components.utils.ensure_compiled(pre_pat)

    assert pat == pre_pat


# utils.extract_listener_params


def test_button_params(button_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(button_listener_callback)
    params = sig.parameters

    button_params, custom_id_params = components.utils.extract_listener_params(sig)
    assert button_params == ()
    assert custom_id_params == (params["foo"], params["bar"])


def test_select_params(select_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(select_listener_callback)
    params = sig.parameters

    select_params, custom_id_params = components.utils.extract_listener_params(sig)
    assert select_params == (params["selected"],)
    assert custom_id_params == (params["foo"], params["bar"])


def test_modal_params(modal_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(modal_listener_callback)
    params = sig.parameters

    modal_params, custom_id_params = components.utils.extract_listener_params(sig)
    assert modal_params == (params["field_A"], params["field_B"])
    assert custom_id_params == (params["foo"], params["bar"])


def test_no_inter():
    async def no_inter_callback(foo: int, bar: str):
        ...

    sig = inspect.signature(no_inter_callback)

    with pytest.raises(TypeError):
        components.utils.extract_listener_params(sig)


# utils.id_spec_from_signature


def test_auto_spec_button(button_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(button_listener_callback)

    spec = components.utils.id_spec_from_signature("name", "|", sig)
    assert spec == "name|{foo}|{bar}"


def test_auto_spec_select(select_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(select_listener_callback)

    spec = components.utils.id_spec_from_signature("name", "|", sig)
    assert spec == "name|{foo}|{bar}"


def test_auto_spec_modal(modal_listener_callback: t.Callable[..., t.Any]):
    sig = inspect.signature(modal_listener_callback)

    spec = components.utils.id_spec_from_signature("name", "|", sig)
    assert spec == "name|{foo}|{bar}"


# utils.id_spec_from_regex


def test_regex_spec():
    pat = re.compile(r"something:(?P<foo>...):(?P<bar>...)")

    spec = components.utils.id_spec_from_regex(pat)
    assert spec == "something:{foo}:{bar}"
