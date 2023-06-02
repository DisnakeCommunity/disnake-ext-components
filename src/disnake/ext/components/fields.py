"""Field implementations extending ``attr.field``."""

from __future__ import annotations

import enum
import functools
import typing

import attr
import typing_extensions

if typing.TYPE_CHECKING:
    from disnake.ext.components.api import parser as parser_api

__all__: typing.Sequence[str] = ("field",)


_T = typing_extensions.TypeVar("_T", default=typing.Any)


class FieldMetadata(enum.Enum):
    """Enum containing keys for field metadata."""

    PARSER = enum.auto()
    """Metadata key to store parser information."""
    FIELDTYPE = enum.auto()
    """Metadata key to store field type information. See :class:`FieldType`."""


class FieldType(enum.Flag):
    """Flag containing field metadata values for the field type.

    Note that a field can only ever be one of these types. This is a flag for
    the sole reason of facilitating unions in lookups using :func:`get_fields`.
    """

    INTERNAL = enum.auto()
    """Internal field that does not show up in the component's init signature."""
    CUSTOM_ID = enum.auto()
    """Field parsed into/from the component's custom id."""
    SELECT = enum.auto()
    """Field parsed from a select component's selected values."""
    MODAL = enum.auto()
    """Field parsed from a modal component's modal values."""

    @classmethod
    def ALL(cls) -> FieldType:
        """Meta-value for all field types.

        Mainly intended for use in :func:`get_fields`.
        """
        return functools.reduce(FieldType.__or__, cls)


_ALL_FIELD_TYPES = FieldType.ALL()


def get_parser(field: attr.Attribute[typing.Any]) -> typing.Optional[parser_api.Parser]:
    """Get the user-provided parser of the provided field.

    If the parser was automatically inferred, this will be ``None``.
    """
    return field.metadata.get(FieldMetadata.PARSER)


def get_field_type(
    field: attr.Attribute[typing.Any], default: typing.Optional[FieldType] = None
) -> FieldType:
    """Get the field type of the field.

    If the field wasn't constructed by disnake-ext-components, this will raise.
    """
    if FieldMetadata.FIELDTYPE not in field.metadata:
        if default:
            return default

        msg = (
            f"Field {field.name!r} does not contain the proper metadata to be"
            f" recognised by disnake-ext-components. Please only construct fields"
            f" through functions provided by disnake-ext-components."
            f" See the 'disnake.ext.components.fields' submodule for possibilities."
        )
        raise TypeError(msg)

    return field.metadata[FieldMetadata.FIELDTYPE]


def is_field_of_type(field: attr.Attribute[typing.Any], kind: FieldType) -> bool:
    """Check whether or not a field is marked as internal."""
    set_type = field.metadata.get(FieldMetadata.FIELDTYPE)
    return bool(set_type and set_type & kind)  # Check if not None, then check if match.


def get_fields(
    cls: type,
    /,
    *,
    kind: FieldType = _ALL_FIELD_TYPES,
) -> typing.Sequence[attr.Attribute[typing.Any]]:
    """Get the attributes of an attrs class.

    This is wraps ``attr.fields`` to be less strict typing-wise and has special
    handling for internal fields.

    Parameters
    ----------
    cls:
        The class of which to get the fields.
    kind:
        The kind(s) of fields to return. Can be any combination of
        :class:`FieldType` s.
    """
    return [field for field in attr.fields(cls) if is_field_of_type(field, kind)]


def field(
    default: typing.Union[_T, typing.Literal[attr.NOTHING]] = attr.NOTHING,
    *,
    parser: typing.Optional[parser_api.Parser[_T]] = None,
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
    return attr.field(
        default=typing.cast(_T, default),
        kw_only=True,
        metadata={
            FieldMetadata.FIELDTYPE: FieldType.CUSTOM_ID,
            FieldMetadata.PARSER: parser,
        },
    )


def internal(
    default: _T,
    *,
    frozen: bool = False,
) -> _T:
    """Declare a field as internal.

    This is used internally to differentiate component parameters from user-
    defined custom id parameters.

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
        A new field with the provided default and frozen status.
    """
    setter = attr.setters.frozen if frozen else None
    return attr.field(
        default=default,
        on_setattr=setter,
        metadata={FieldMetadata.FIELDTYPE: FieldType.INTERNAL},
    )
