"""Field implementations extending ``attr.field``."""

from __future__ import annotations

import sys
import typing

import attr
import typing_extensions

if typing.TYPE_CHECKING:
    from disnake.ext.components.api import parser as parser_

__all__: typing.Sequence[str] = ("field",)


_T = typing_extensions.TypeVar("_T", default=typing.Any)


PARSER: typing.Final[str] = sys.intern("parser")
INTERNAL: typing.Final[str] = sys.intern("internal")


def is_internal(field: attr.Attribute[typing.Any]) -> bool:
    """Check whether or not a field is marked as internal."""
    return bool(field.metadata.get(INTERNAL))


def get_fields(
    cls: type,
    /,
    *,
    internal: bool = False,
) -> typing.Sequence[attr.Attribute[typing.Any]]:
    """Get the attributes of an attrs class.

    This is wraps ``attr.fields`` to be less strict typing-wise and has special
    handling for internal fields.

    Parameters
    ----------
    cls:
        The class of which to get the fields.
    internal:
        Whether or not to include internal fields. Defaults to False.
    """
    fields = attr.fields(cls)
    if internal:
        return fields

    return [field for field in fields if not is_internal(field)]


def field(
    default: _T,
    *,
    parser: typing.Optional[parser_.Parser[_T]] = None,
) -> _T:
    """Define a custom ID field for the component.

    The type annotation for this field is used to parse incoming custom ids.

    .. note::
        In most cases, simply using a typehint will suffice to define a field.
        This function is generally only needed if you wish to supply a default
        value or custom parser.

    Parameters
    ----------
    default:
        The default value for this field. The type of the default should match
        that of the type annotation.
    parser:
        The parser to use for converting this field to and from a string.
        The type of the parser should match that of the type annotation.

    Returns
    -------
    attr.Field
        A new field with the provided default and parser. Note that a field
        created this way always has ``kw_only=True`` set.
    """
    return attr.field(default=default, kw_only=True, metadata={PARSER: parser})


def internal(  # noqa: D417
    default: _T,
    *,
    init: typing.Literal[False] = False,  # noqa: ARG001
    frozen: bool = False,
) -> _T:
    """Declare a field as internal.

    This automatically makes it not appear inside the init signature for the
    component, and allows marking the field as frozen.

    Parameters
    ----------
    default:
        The default value for this field. The type of the default should match
        that of the type annotation.
    frozen:
        Whether or not the field should be marked frozen. A frozen field cannot
        be modified after the class has been created.

    Returns
    -------
    attr.Field
        A new field with the provided default and frozen status. Note that an
        internal field always has ``init=False`` set.
    """
    # NOTE: The init arg is *required* in the signature for typecheckers to
    #       pick up on it. If it weren't there, each internal field would have
    #       to manually declare ``init=False``.

    setter = attr.setters.frozen if frozen else None
    return attr.field(
        default=default,
        init=False,
        on_setattr=setter,
        metadata={INTERNAL: True},
    )
