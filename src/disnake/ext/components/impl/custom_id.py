"""Implementation of custom id classes."""

from __future__ import annotations

import typing

from disnake.ext.components import fields as field_impl
from disnake.ext.components.api import component as component_api
from disnake.ext.components.api import custom_id as custom_id_api
from disnake.ext.components.internal import regex

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = ("CustomID", "AutoID")

# TODO: regex custom id


AUTO_ID_DEFAULT: typing.Final[str] = "AUTO_ID"


class CustomID(str, custom_id_api.CustomID):
    """A custom id containing information on a component.

    Generally, it is advised to use :class:`AutoID` instead, and a matching
    instance of this class will be constructed internally.

    Parameters
    ----------
    fields: :class:`str`
        The fields to use for this custom id. These **must** be present on the
        component class this custom id is for, otherwise it will lead to errors
        when building component instances. Validation can be done using
        :meth:`validate`.
    name: str
        The name that should be used to represent the component.
    sep: str
        The delimiter to use between the custom id name and fields.
        Defaults to ``"|"``
    """

    name: str
    fields: typing.Sequence[str]
    sep: str
    pattern: typing.Pattern[str]

    @staticmethod
    def make_spec(*fields: str, name: str, sep: str = "|") -> str:
        """Create a formattable string that can be used to build a custom id.

        Parameters
        ----------
        fields:
            The names of the fields that should be used in this custom id.
        name:
            The name that should be used to represent the component.
        sep:
            The delimiter to use between the custom id name and fields.
            Defaults to ``"|"``

        Returns
        -------
        str:
            A formattable string intended for use with :meth:`str.format_map`.
            The format keys are the names of the passed fields.
        """
        if not fields:
            return name

        return name + sep + sep.join(f"{{{id_field}}}" for id_field in fields)

    def __new__(  # noqa: D102
        cls, *fields: str, name: str, sep: str = "|"
    ) -> typing_extensions.Self:
        spec = cls.make_spec(*fields, name=name, sep=sep)
        self = super().__new__(cls, spec)

        self.name = name
        self.fields = fields
        self.sep = sep
        self.pattern = regex.format_to_pattern(spec)

        return self

    @classmethod
    def from_component(  # noqa: D102
        cls,
        component: type[component_api.RichComponent],
        /,
        *,
        name: typing.Optional[str] = None,
        sep: str = "|",
    ) -> typing_extensions.Self:
        # <<Docstring inherited from custom_id_api.CustomID>>

        fields = field_impl.get_fields(component)
        return cls(
            *[field.name for field in fields],
            name=name or component.__name__,
            sep=sep,
        )

    @classmethod
    def from_auto_id(
        cls,
        component: type[component_api.RichComponent],
        auto_id: AutoID,
    ) -> typing_extensions.Self:
        """Create a complete custom id object from a :class:`AutoID`.

        Parameters
        ----------
        component:
            The component for which this custom id is to be created.
        auto_id:
            The auto_id to turn into a new complete custom id.

        Returns
        -------
        CustomID:
            The newly created and complete :class:`CustomID`.
        """
        return cls.from_component(
            component,
            name=auto_id.name or component.__name__,
            sep=auto_id.sep or auto_id.default_sep,
        )

    def validate(  # noqa: D102
        self, component: type[component_api.RichComponent]
    ) -> None:
        # <<Docstring inherited from custom_id_api.CustomID>>

        fields = {field.name for field in field_impl.get_fields(component)}

        invalid_fields = fields - set(self.fields)

        if invalid_fields:
            invalid_str = ", ".join(map(repr, invalid_fields))
            msg = (
                f"Fields {invalid_str} were defined in the custom id for component"
                f" {component.__name__}, but are not actually defined on the class."
            )
            raise ValueError(msg)

    def complete(self, component: component_api.RichComponent) -> str:  # noqa: D102
        # <<Docstring inherited from custom_id_api.CustomID>>

        return self.format_map(
            {id_field: getattr(component, id_field) for id_field in self.fields}
        )

    def check_name(self, custom_id: str) -> bool:  # noqa: D102
        # <<Docstring inherited from custom_id_api.CustomID>>

        return custom_id.startswith(self.name)

    @typing.overload
    def match(
        self, custom_id: str, *, strict: typing.Literal[False] = False
    ) -> typing.Optional[typing.Match[str]]:
        ...

    @typing.overload
    def match(
        self, custom_id: str, *, strict: typing.Literal[True]
    ) -> typing.Match[str]:
        ...

    def match(  # noqa: D102
        self, custom_id: str, *, strict: bool = False
    ) -> typing.Optional[typing.Match[str]]:
        # <<Docstring inherited from custom_id_api.CustomID>>

        match = self.pattern.fullmatch(custom_id)
        if not match and strict:
            # TODO: Custom error type, maybe warn instead.
            msg = (
                f"Encountered a custom id with valid name {self.name}, but its"
                " parameters did not match that of the corresponding component."
                f"\n(got: {custom_id}, pattern: {self.pattern.pattern})"
            )
            raise RuntimeError(msg)

        return match


class AutoID(str):
    """A custom id that is automatically built from the component's fields.

    By default, the name defaults to that of the component, and the separator
    defaults to :attr:`AutoID.default_sep`. Initially, this separator is set to
    ``"|"``, but this can be overwritten.

    Parameters
    ----------
    name: typing.Optional[:class:`str`]
        The name to represent the component. Default's the the component class'
        name.
    sep: typing.Optional[str]
        The delimiter used between the custom id name and fields. Defaults to
        :attr:`AutoID.default_sep`.
    """

    __slots__: typing.Sequence[str] = ("name", "sep")

    default_sep: typing.ClassVar[str] = "|"

    name: typing.Optional[str]
    sep: typing.Optional[str]

    def __new__(  # noqa: D102
        cls,
        *,
        name: typing.Optional[str] = None,
        sep: typing.Optional[str] = None,
    ) -> typing_extensions.Self:
        self = super().__new__(cls, AUTO_ID_DEFAULT)

        self.name = name
        self.sep = sep
        return self
