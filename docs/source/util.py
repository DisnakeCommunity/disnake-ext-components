"""Small utilities for Sphinx documentation."""

import collections.abc
import importlib.util
import inspect
import os
import re
import subprocess
import sys
import typing

__all__ = (
    "git",
    "get_git_ref",
    "get_module_path",
    "make_linkcode_resolver",
)


def git(*args: str) -> str:
    """Run a git command and return the output."""
    return subprocess.check_output(["git", *args], text=True).strip()  # noqa: S603 S607


def get_git_ref() -> str:
    """Return the current git reference."""
    # Current git reference. Uses branch/tag name if found, otherwise uses commit hash
    git_ref = git("name-rev", "--name-only", "--no-undefined", "HEAD")
    return re.sub(r"^(remotes/[^/]+|tags)/", "", git_ref)


def get_module_path() -> str:
    """Get the filepath for the module."""
    _spec = importlib.util.find_spec("disnake.ext.components")
    if not (_spec and _spec.origin):
        raise RuntimeError  # this should never happen

    return os.path.dirname(_spec.origin)


def make_linkcode_resolver(
    module_path: str, repo_url: str, git_ref: str
) -> typing.Callable[[str, typing.Mapping[str, typing.Any]], typing.Optional[str]]:
    """Return a linkcode resolver for the provided module path and repo data."""

    def linkcode_resolve(
        domain: str, info: typing.Mapping[str, typing.Any]
    ) -> typing.Optional[str]:
        if domain != "py":
            return None

        try:
            obj: typing.Any = sys.modules[info["module"]]
            for part in info["fullname"].split("."):
                obj = getattr(obj, part)
            obj = inspect.unwrap(obj)

            if isinstance(obj, property):
                obj = inspect.unwrap(obj.fget)  # pyright: ignore

            path: typing.Any = inspect.getsourcefile(obj)
            path = os.path.relpath(path, start=module_path)
            src, lineno = inspect.getsourcelines(obj)

        except Exception:  # noqa: BLE001
            return None

        path = f"{path}#L{lineno}-L{lineno + len(src) - 1}"
        return f"{repo_url}/blob/{git_ref}/src/disnake/ext/components/{path}"

    return linkcode_resolve


def make_generic(cls: type) -> None:
    """Hacky way to get around runtime inconsistencies in typehinting.

    e.g. attrs.Attribute is generic during type-checking, but not generic at runtime.
    """
    if hasattr(cls, "__class_getitem__"):
        raise TypeError

    def __class_getitem__(params: ...) -> ...:
        return typing._GenericAlias(cls, params)  # pyright: ignore

    cls.__class_getitem__ = __class_getitem__  # pyright: ignore


def prettify_typehint(obj: object, aliases: typing.Dict[object, str]) -> object:
    """Make typehints render nicer in rendered sphinx docs."""
    # If we've already registered some way to display the obj, use that.
    origin = typing.get_origin(obj)
    if origin in aliases:
        return aliases[origin]

    if origin is collections.abc.Callable:
        args, ret = typing.get_args(obj)
        new_args = [prettify_typehint(arg, aliases) for arg in args]
        new_args.append(prettify_typehint(ret, aliases))

    # If typevar, just display the name
    elif isinstance(obj, typing.TypeVar):
        return f"``{obj.__name__}``"  # Maybe stip underscores?

    # Otherwise, check if it has args
    else:
        new_args = [prettify_typehint(arg, aliases) for arg in typing.get_args(obj)]

    try:
        return obj.copy_with(tuple(new_args))  # pyright: ignore

    # If not, return as-is
    except AttributeError:
        return obj
